"""evidence_kind on manifest claims gates which runner template may witness them."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

AFF = Path(__file__).resolve().parents[1] / "bin" / "aff"
CLAIM = "claim-widget"
ORACLE_REL = "tests/test_widget.py"
NODE = f"{ORACLE_REL}::test_widget"
ORACLE = b"def test_widget():\n    from app import value\n    assert value == 1\n"
APP_RED = b"value = 0\n"
APP_GREEN = b"value = 1\n"
ALLOW = (
    b'owner namespaces="affidavit-amendment" '
    b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKeyOneaaaaaaaaaaaaaaaaaaa\n"
)


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    assert result.returncode == 0, f"git {args!r} failed\n{result.stderr}"
    return result.stdout.strip()


def _manifest(evidence_kind: str | None, runner: list[str] | None) -> dict:
    claim: dict = {
        "id": CLAIM,
        "text": "value is one",
        "tests": [NODE],
        "oracle_hashes": {ORACLE_REL: "sha256:" + hashlib.sha256(ORACLE).hexdigest()},
    }
    if evidence_kind is not None:
        claim["evidence_kind"] = evidence_kind
    document: dict = {"claims": [claim], "amendments": []}
    if runner is not None:
        document["runner"] = list(runner)
    return document


def _write(root: Path, *, app: bytes, manifest: dict) -> None:
    affidavit = root / ".affidavit"
    affidavit.mkdir(exist_ok=True)
    (affidavit / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (affidavit / "allowed_signers").write_bytes(ALLOW)
    (root / "pytest.ini").write_text("[pytest]\n")
    oracle = root / ORACLE_REL
    oracle.parent.mkdir(parents=True, exist_ok=True)
    oracle.write_bytes(ORACLE)
    (root / "app.py").write_bytes(app)


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD")


def _repo(root: Path, evidence_kind: str | None, runner: list[str] | None = None) -> str:
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "core.autocrlf", "false")
    _git(root, "config", "commit.gpgsign", "false")
    manifest = _manifest(evidence_kind, runner)
    _write(root, app=APP_RED, manifest=manifest)
    _commit(root, "red")
    _git(root, "checkout", "-qb", "phase/widget")
    _write(root, app=APP_GREEN, manifest=manifest)
    return _commit(root, "green")


def _verdict(root: Path, head: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(AFF), "verdict", "--at", head, CLAIM],
        cwd=str(root),
        capture_output=True,
        text=True,
    )


def _payload(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def _interaction_runner() -> list[str]:
    proc = subprocess.run(
        [str(AFF), "runner-template", "interaction"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    runner = json.loads(proc.stdout)
    assert isinstance(runner, list) and runner
    return runner


def test_r1_manifest_claim_may_declare_evidence_kind(tmp_path: Path) -> None:
    """R1: A manifest claim may declare evidence_kind as unit, integration, or interaction."""
    for kind in ("unit", "integration"):
        root = tmp_path / kind
        head = _repo(root, kind)
        proc = _verdict(root, head)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _payload(proc)["result"] == "pass"

    root = tmp_path / "bogus"
    head = _repo(root, "bogus")
    proc = _verdict(root, head)
    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "evidence_kind" in proc.stderr + proc.stdout
    if proc.stdout.strip().startswith("{"):
        assert _payload(proc).get("result") != "pass"


def test_r2_interaction_claim_fails_under_default_unit_runner(tmp_path: Path) -> None:
    """R2: aff verdict fails an interaction claim whose witness runs under the default unit runner."""
    root = tmp_path / "repo"
    head = _repo(root, "interaction")
    proc = _verdict(root, head)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [
        {
            "id": CLAIM,
            "result": "fail",
            "reason": "evidence_kind: interaction requires an interaction runner template",
        }
    ]


def test_r3_interaction_claim_passes_under_interaction_runner(tmp_path: Path) -> None:
    """R3: aff verdict passes an interaction claim whose witness runs under the interaction template."""
    runner = _interaction_runner()
    root = tmp_path / "repo"
    head = _repo(root, "interaction", runner)
    proc = _verdict(root, head)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _payload(proc) == {"result": "pass", "claims": [{"id": CLAIM, "result": "pass"}]}
