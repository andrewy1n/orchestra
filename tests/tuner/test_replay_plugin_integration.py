from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from orchestra.canon import extensions
from orchestra.canon.project_config import DEFAULT_RUNNER, ProjectConfig
from orchestra.canon.types import JsonObject, get_object, get_string
from orchestra.tuner.audit import run_audit
from orchestra.tuner.lint import find_new_skips
from orchestra.tuner.technique import ReplayRequest, TechniqueResult, replay_at_revision
from orchestra.tuner.verdict import run_verdict

CLAIM = "claim-replay-plugin"
NODE = "tests/test_plugin.py::test_plugin"
ORACLE = "tests/test_plugin.py"
ORACLE_BYTES = b"def test_plugin():\n    assert True\n"


class ReplayPlugin:
    calls: ClassVar[list[tuple[str, str]]] = []

    def validate_config(self, config: ProjectConfig) -> None:
        del config

    def execution_definition(self, config: ProjectConfig) -> dict[str, object]:
        del config
        return {"engine": "replay-test-v1"}

    def validate_result(self, result: TechniqueResult) -> None:
        del result

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


class UntrustedReplayPlugin:
    calls: ClassVar[int] = 0

    def validate_config(self, config: ProjectConfig) -> None:
        del config

    def execution_definition(self, config: ProjectConfig) -> dict[str, object]:
        del config
        return {"engine": "untrusted-replay-test-v1"}

    def validate_result(self, result: TechniqueResult) -> None:
        del result

    def replay(self, request: ReplayRequest) -> dict[str, str]:
        UntrustedReplayPlugin.calls += 1
        return {test_id: "passed" for test_id in request.test_ids}


def _replay_plugin_id(payload: JsonObject) -> str:
    identity = get_object(payload, "replay_identity")
    assert identity is not None, "verdict is missing replay_identity"
    plugin_id = get_string(identity, "plugin_id")
    assert plugin_id is not None, "replay_identity is missing plugin_id"
    return plugin_id


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _write_revision(root: Path, behavior: str) -> None:
    (root / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["unit"]\n'
        f"[verify.unit]\nrunner = {json.dumps(DEFAULT_RUNNER)}\n"
        '[verify.replay]\ntechnique = "external-replay"\n',
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
    entries = []
    for plugin_id, factory in (
        ("external-replay", ReplayPlugin),
        ("untrusted-replay", UntrustedReplayPlugin),
    ):
        metadata_entries = (
            SimpleNamespace(name="version", value="1", group=extensions.PLUGIN_API_GROUP),
            SimpleNamespace(name=plugin_id, value="{}", group=extensions.PLUGIN_CONFIG_GROUP),
        )
        entries.append(
            SimpleNamespace(
                name=plugin_id,
                value=f"{plugin_id}:Plugin",
                dist=SimpleNamespace(
                    metadata={"Name": plugin_id},
                    version="1.0",
                    entry_points=metadata_entries,
                ),
                load=lambda factory=factory: factory,
            )
        )
    monkeypatch.setattr(
        extensions.metadata,
        "entry_points",
        lambda *, group: tuple(entries) if group == "orchestra.tuner.verify" else (),
    )


def test_verdict_and_audit_replay_registered_plugin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ReplayPlugin.calls.clear()
    _register_plugin(monkeypatch)
    root = tmp_path / "repo"
    base, head = _repo(root, "failure", "pass")

    verdict = run_verdict(root, head, base, [CLAIM])
    audit = run_audit(root, base, head, max_mutants=0)

    assert verdict["result"] == "pass"
    assert verdict["claims"] == [{"id": CLAIM, "result": "pass"}]
    assert _replay_plugin_id(verdict) == "external-replay"
    assert audit["advisory"] is True
    assert any(behavior == "failure" for _, behavior in ReplayPlugin.calls)
    assert ReplayPlugin.calls.count(("HEAD", "pass")) >= 2


def test_verdict_uses_replay_technique_from_trusted_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _register_plugin(monkeypatch)
    UntrustedReplayPlugin.calls = 0
    root = tmp_path / "repo"
    base, head = _repo(root, "failure", "pass")
    config_path = root / "orchestra.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace("external-replay", "untrusted-replay"),
        encoding="utf-8",
    )
    _git(root, "add", "orchestra.toml")
    _git(root, "commit", "-qm", "select untrusted replay")
    head = _git(root, "rev-parse", "HEAD")

    verdict = run_verdict(root, head, base, [CLAIM])

    assert verdict["result"] == "pass"
    assert _replay_plugin_id(verdict) == "external-replay"
    assert UntrustedReplayPlugin.calls == 0


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
