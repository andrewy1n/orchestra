from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from orchestra.canon import extensions
from orchestra.tuner.audit import run_audit
from orchestra.tuner.lint import find_new_skips
from orchestra.tuner.technique import ReplayRequest, replay_at_revision
from orchestra.tuner.verdict import run_verdict

CLAIM = "claim-replay-plugin"
NODE = "tests/test_plugin.py::test_plugin"
ORACLE = "tests/test_plugin.py"
ORACLE_BYTES = b"def test_plugin():\n    assert True\n"


class ReplayPlugin:
    calls: ClassVar[list[tuple[str, str]]] = []

    def replay(self, request: ReplayRequest) -> dict[str, str]:
        behavior = subprocess.run(
            ["git", "-C", str(request.root), "show", f"{request.revision}:behavior"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.calls.append((request.revision, behavior))
        outcomes = {
            "failure": "assertion_failed",
            "pass": "passed",
            "error": "errored",
            "skip": "not_run",
        }
        return {test_id: outcomes[behavior] for test_id in request.test_ids}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _write_revision(root: Path, behavior: str) -> None:
    (root / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["unit"]\n[verify.replay]\ntechnique = "external-replay"\n',
        encoding="utf-8",
    )
    digest = hashlib.sha256(ORACLE_BYTES).hexdigest()
    manifest = {
        "claims": [
            {
                "id": CLAIM,
                "text": "plugin replay reports the expected result",
                "tests": [NODE],
                "oracle_hashes": {ORACLE: f"sha256:{digest}"},
            }
        ],
        "amendments": [],
    }
    (root / ".tuner" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "behavior").write_text(f"{behavior}\n", encoding="utf-8")
    (root / ORACLE).parent.mkdir(parents=True, exist_ok=True)
    (root / ORACLE).write_bytes(ORACLE_BYTES)


def _repo(root: Path, base_behavior: str, head_behavior: str) -> tuple[str, str]:
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "plugin-test@example.com")
    _git(root, "config", "user.name", "plugin test")
    _git(root, "config", "commit.gpgsign", "false")
    (root / ".tuner").mkdir()
    (root / ".tuner" / "allowed_signers").write_text("", encoding="utf-8")
    (root / "module.py").write_text("value = 0\n", encoding="utf-8")
    _write_revision(root, base_behavior)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "base")
    base = _git(root, "rev-parse", "HEAD")
    (root / "module.py").write_text("value = 1\n", encoding="utf-8")
    _write_revision(root, head_behavior)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "head")
    return base, _git(root, "rev-parse", "HEAD")


def _register_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    entry = SimpleNamespace(
        name="external-replay",
        value="external_replay:Plugin",
        dist=SimpleNamespace(metadata={"Name": "external-replay"}, version="1.0"),
        load=lambda: ReplayPlugin,
    )
    monkeypatch.setattr(extensions.metadata, "entry_points", lambda *, group: (entry,))


def test_verdict_and_audit_replay_registered_plugin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ReplayPlugin.calls.clear()
    _register_plugin(monkeypatch)
    root = tmp_path / "repo"
    base, head = _repo(root, "failure", "pass")

    verdict = run_verdict(root, head, base, [CLAIM])
    audit = run_audit(root, base, head, max_mutants=0)

    assert verdict == {"result": "pass", "claims": [{"id": CLAIM, "result": "pass"}]}
    assert audit["advisory"] is True
    assert any(behavior == "failure" for _, behavior in ReplayPlugin.calls)
    assert ReplayPlugin.calls.count(("HEAD", "pass")) >= 2


def test_error_and_skip_outcomes_remain_distinct_in_new_skip_lint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ReplayPlugin.calls.clear()
    _register_plugin(monkeypatch)
    root = tmp_path / "repo"
    base, head = _repo(root, "error", "skip")

    error = replay_at_revision(root, base, (NODE,), ())
    skipped = replay_at_revision(root, head, (NODE,), ())
    findings = find_new_skips(root, base, head, claim_id=CLAIM)

    assert error == {NODE: "errored"}
    assert skipped == {NODE: "not_run"}
    assert findings == [NODE]
