"""Standalone claim authoring: claim add, freeze, lint claims, human-signed claims."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

VERIFY = [sys.executable, str(Path(__file__).resolve().parents[2] / "bin" / "orchestra"), "verify"]
ORACLE_REL = "tests/test_widget.py"
NODE = f"{ORACLE_REL}::test_widget"
ORACLE = b"def test_widget():\n    from app import value\n    assert value == 1\n"
APP_RED = b"value = 0\n"
APP_GREEN = b"value = 1\n"
ALLOW = (
    b'owner namespaces="tuner-amendment" '
    b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKeyOneaaaaaaaaaaaaaaaaaaa\n"
)
HUMAN_ID = "human-claim"
HUMAN_TEXT = "the reviewer accepts the widget copy"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join([str(Path(sys.executable).parent), "/usr/bin", "/bin"])
    return env


def _tuner(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*VERIFY, *args],
        cwd=str(cwd) if cwd else None,
        env=_env(),
        capture_output=True,
        text=True,
    )


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {args!r} failed\n{result.stderr}")
    return result


def _init(root: Path) -> None:
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "core.autocrlf", "false")
    _git(root, "config", "commit.gpgsign", "false")


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def _manifest_path(root: Path) -> Path:
    return root / ".tuner" / "manifest.json"


def _read_manifest(root: Path) -> dict:
    return json.loads(_manifest_path(root).read_text())


def _write_manifest(root: Path, document: dict) -> None:
    _manifest_path(root).parent.mkdir(parents=True, exist_ok=True)
    _manifest_path(root).write_text(json.dumps(document, indent=2) + "\n")


def _generate_key(directory: Path, name: str) -> tuple[Path, str]:
    key_path = directory / name
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(key_path), "-q"],
        check=True,
        capture_output=True,
    )
    public = subprocess.check_output(
        ["ssh-keygen", "-y", "-f", str(key_path)],
        text=True,
    ).strip()
    return key_path, " ".join(public.split()[:2])


def _human_allowlist(blob: str) -> bytes:
    return f'reviewer namespaces="tuner-claim" {blob}\n'.encode()


def _human_payload(claim_id: str, text: str) -> bytes:
    return f"tuner-claim v1\nclaim: {claim_id}\ntext: {text}\n".encode()


def _sign_human(key_path: Path, claim_id: str, text: str) -> str:
    completed = subprocess.run(
        ["ssh-keygen", "-Y", "sign", "-f", str(key_path), "-n", "tuner-claim"],
        input=_human_payload(claim_id, text),
        check=True,
        capture_output=True,
    )
    return completed.stdout.decode("utf-8")


def _human_repo(root: Path, allowlist: bytes, claim_extra: dict) -> tuple[str, str]:
    _init(root)
    tuner = root / ".tuner"
    tuner.mkdir()
    (tuner / "allowed_signers").write_bytes(allowlist)
    _write_manifest(root, {"claims": [], "amendments": []})
    (root / "README.md").write_text("fixture\n")
    base = _commit(root, "base")
    claim = {
        "id": HUMAN_ID,
        "text": HUMAN_TEXT,
        "tests": [],
        "oracle_hashes": {},
        "witness": "human",
    }
    claim.update(claim_extra)
    _write_manifest(root, {"claims": [claim], "amendments": []})
    head = _commit(root, "human claim")
    return base, head


def _human_verdict(root: Path, base: str, head: str) -> subprocess.CompletedProcess[str]:
    return _tuner("verdict", "--cwd", str(root), "--base", base, "--at", head, HUMAN_ID)


def _payload(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def _reason(proc: subprocess.CompletedProcess[str]) -> str:
    claims = _payload(proc)["claims"]
    assert len(claims) == 1, claims
    return claims[0]["reason"]


def test_r1_claim_add_writes_manifest_entry_standalone(tmp_path):
    """R1: orchestra verify claim add appends a claim to the committed manifest format without orchestra."""
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    proc = _tuner(
        "claim",
        "add",
        "--cwd",
        str(fresh),
        "--id",
        "claim-a",
        "--text",
        "value is one",
        "--test",
        NODE,
        "--test",
        f"{ORACLE_REL}::test_other",
    )
    assert proc.returncode == 0, proc.stderr
    document = _read_manifest(fresh)
    assert document["amendments"] == []
    assert document["claims"] == [
        {
            "id": "claim-a",
            "text": "value is one",
            "tests": [NODE, f"{ORACLE_REL}::test_other"],
            "oracle_hashes": {},
        }
    ]

    existing = tmp_path / "existing"
    existing.mkdir()
    prior = {
        "id": "claim-old",
        "text": "old claim",
        "tests": ["tests/test_old.py::test_old"],
        "oracle_hashes": {"tests/test_old.py": "sha256:" + "ab" * 32},
    }
    _write_manifest(
        existing,
        {
            "claims": [prior],
            "amendments": [],
            "runner": ["python3", "-m", "pytest", "{tests}"],
            "support_files": ["conftest.py"],
        },
    )
    proc = _tuner(
        "claim",
        "add",
        "--cwd",
        str(existing),
        "--id",
        "claim-new",
        "--text",
        "new claim",
        "--test",
        NODE,
    )
    assert proc.returncode == 0, proc.stderr
    document = _read_manifest(existing)
    assert document["runner"] == ["python3", "-m", "pytest", "{tests}"]
    assert document["support_files"] == ["conftest.py"]
    assert document["claims"][0] == prior
    assert document["claims"][1]["id"] == "claim-new"
    assert document["claims"][1]["tests"] == [NODE]
    assert document["claims"][1]["oracle_hashes"] == {}

    before = _manifest_path(existing).read_bytes()
    proc = _tuner(
        "claim",
        "add",
        "--cwd",
        str(existing),
        "--id",
        "claim-new",
        "--text",
        "different",
        "--test",
        NODE,
    )
    assert proc.returncode != 0
    assert _manifest_path(existing).read_bytes() == before


def test_r2_freeze_records_exact_oracle_hashes(tmp_path):
    """R2: orchestra verify freeze writes sha256 of each oracle file into oracle_hashes."""
    other = b"def test_gadget():\n    assert True\n"
    (tmp_path / "tests").mkdir()
    (tmp_path / ORACLE_REL).write_bytes(ORACLE)
    (tmp_path / "tests" / "test_gadget.py").write_bytes(other)
    _write_manifest(
        tmp_path,
        {
            "claims": [
                {
                    "id": "claim-a",
                    "text": "value is one",
                    "tests": [NODE, f"{ORACLE_REL}::test_second"],
                    "oracle_hashes": {ORACLE_REL: "sha256:stale", "gone.py": "sha256:stale"},
                },
                {
                    "id": "claim-b",
                    "text": "gadget works",
                    "tests": ["tests/test_gadget.py::test_gadget"],
                    "oracle_hashes": {},
                },
            ],
            "amendments": [],
        },
    )
    proc = _tuner("freeze", "--cwd", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    claims = {claim["id"]: claim for claim in _read_manifest(tmp_path)["claims"]}
    assert claims["claim-a"]["oracle_hashes"] == {ORACLE_REL: _sha256(ORACLE)}
    assert claims["claim-b"]["oracle_hashes"] == {"tests/test_gadget.py": _sha256(other)}

    (tmp_path / ORACLE_REL).unlink()
    before = _manifest_path(tmp_path).read_bytes()
    proc = _tuner("freeze", "--cwd", str(tmp_path), "claim-a")
    assert proc.returncode != 0
    assert _manifest_path(tmp_path).read_bytes() == before
    proc = _tuner("freeze", "--cwd", str(tmp_path), "no-such-claim")
    assert proc.returncode != 0
    assert _manifest_path(tmp_path).read_bytes() == before


def test_r2_standalone_add_freeze_verdict_passes(tmp_path):
    """R2: claim add + freeze + verdict passes end to end with no orchestra on PATH."""
    root = tmp_path / "repo"
    _init(root)
    (root / "pytest.ini").write_text("[pytest]\n")
    (root / "tests").mkdir()
    (root / ORACLE_REL).write_bytes(ORACLE)
    (root / "app.py").write_bytes(APP_RED)
    (root / ".tuner").mkdir()
    (root / ".tuner" / "allowed_signers").write_bytes(ALLOW)

    added = _tuner(
        "claim",
        "add",
        "--cwd",
        str(root),
        "--id",
        "claim-widget",
        "--text",
        "value is one",
        "--test",
        NODE,
    )
    assert added.returncode == 0, added.stderr
    frozen = _tuner("freeze", "--cwd", str(root))
    assert frozen.returncode == 0, frozen.stderr
    base = _commit(root, "red")

    (root / "app.py").write_bytes(APP_GREEN)
    head = _commit(root, "green")

    proc = _tuner("verdict", "--cwd", str(root), "--base", base, "--at", head, "claim-widget")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _payload(proc)["result"] == "pass"


def test_r3_lint_claims_reports_compound_claim(tmp_path):
    """R3: orchestra verify lint claims reports a compound claim and leaves an atomic claim alone."""
    _write_manifest(
        tmp_path,
        {
            "claims": [
                {
                    "id": "claim-atomic",
                    "text": "value is one",
                    "tests": [NODE],
                    "oracle_hashes": {},
                },
                {
                    "id": "claim-multi",
                    "text": "value is one and the widget renders",
                    "tests": [NODE],
                    "oracle_hashes": {},
                },
            ],
            "amendments": [],
        },
    )
    proc = _tuner("lint", "claims", "--cwd", str(tmp_path))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "claim-multi: compound claim" in proc.stdout.splitlines()
    assert "claim-atomic" not in proc.stdout


def test_r4_verdict_accepts_valid_human_signature(tmp_path):
    """R4: orchestra verify verdict passes a human claim whose signature verifies against the allowlist."""
    key, blob = _generate_key(tmp_path, "reviewer_key")
    signature = _sign_human(key, HUMAN_ID, HUMAN_TEXT)
    root = tmp_path / "repo"
    base, head = _human_repo(root, _human_allowlist(blob), {"signature": signature})
    proc = _human_verdict(root, base, head)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _payload(proc)["result"] == "pass"


def test_r5_verdict_rejects_missing_human_signature(tmp_path):
    """R5: orchestra verify verdict fails a human claim with a missing or empty signature."""
    _, blob = _generate_key(tmp_path, "reviewer_key")
    allow = _human_allowlist(blob)
    for index, extra in enumerate(({}, {"signature": ""})):
        root = tmp_path / f"repo{index}"
        base, head = _human_repo(root, allow, extra)
        proc = _human_verdict(root, base, head)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert _payload(proc)["result"] == "fail"
        assert _reason(proc) == "human signature missing"


def test_r5_verdict_rejects_invalid_human_signature(tmp_path):
    """R5: orchestra verify verdict fails a human claim signed by an unlisted key or altered after signing."""
    key, blob = _generate_key(tmp_path, "reviewer_key")
    rogue, _ = _generate_key(tmp_path, "rogue_key")
    allow = _human_allowlist(blob)
    variants = {
        "unlisted-key": _sign_human(rogue, HUMAN_ID, HUMAN_TEXT),
        "altered-text": _sign_human(key, HUMAN_ID, "the reviewer rejects the widget copy"),
    }
    for name, signature in variants.items():
        root = tmp_path / name
        base, head = _human_repo(root, allow, {"signature": signature})
        proc = _human_verdict(root, base, head)
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert _payload(proc)["result"] == "fail"
        assert _reason(proc) == "human signature invalid"
