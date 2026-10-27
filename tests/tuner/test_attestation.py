"""Signed verdict attestation (R1–R4)."""

from __future__ import annotations

import importlib
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

COMMIT_A = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
COMMIT_B = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
MANIFEST_A = "sha256:" + ("11" * 32)
MANIFEST_B = "sha256:" + ("22" * 32)
RUNNER_DIGEST = "sha256:" + ("33" * 32)
CLAIM_ID = "claim-widget"


def _attestation():
    try:
        return importlib.import_module("affidavit.attestation")
    except ModuleNotFoundError:
        return None


def _generate_key(directory: Path, name: str = "id_ed25519") -> tuple[Path, str]:
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
    blob = " ".join(public.split()[:2])
    return key_path, blob


def _allowlist(principal: str, blob: str) -> bytes:
    return f'{principal} namespaces="affidavit-verdict" {blob}\n'.encode()


def _verdict_body(
    *,
    commit: str = COMMIT_A,
    manifest_hash: str = MANIFEST_A,
    runner_digest: str = RUNNER_DIGEST,
    claims: list[dict] | None = None,
) -> dict:
    return {
        "commit": commit,
        "manifest_hash": manifest_hash,
        "runner_digest": runner_digest,
        "claims": list(
            claims
            if claims is not None
            else [{"id": CLAIM_ID, "result": "pass"}]
        ),
    }


def _corrupt(signature: str) -> str:
    lines = signature.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith("-----") or not line.strip():
            continue
        chars = list(line)
        for pos, char in enumerate(chars):
            if char.isalnum():
                chars[pos] = "A" if char != "A" else "B"
                lines[index] = "".join(chars)
                return "".join(lines)
    return signature + "x"


def test_emit_signed_attestation_includes_commit_manifest_runner_and_claims(
    tmp_path: Path,
) -> None:
    """R1: emit produces an SSH-signed attestation whose payload includes commit,
    manifest hash, runner digest, and per-claim results."""
    mod = _attestation()
    assert mod is not None, "affidavit.attestation must exist"
    key, blob = _generate_key(tmp_path)
    allow = _allowlist("ci", blob)
    body = _verdict_body(
        claims=[
            {"id": CLAIM_ID, "result": "pass"},
            {"id": "claim-other", "result": "fail"},
        ]
    )
    signed = mod.emit(body, key_path=key)
    assert isinstance(signed, dict)
    assert signed.get("signature"), "emit must attach an SSH signature"
    assert signed["commit"] == COMMIT_A
    assert signed["manifest_hash"] == MANIFEST_A
    assert signed["runner_digest"] == RUNNER_DIGEST
    assert signed["claims"] == body["claims"]

    payload = mod.canonical_payload(signed)
    assert isinstance(payload, (bytes, bytearray))
    text = bytes(payload).decode("utf-8")
    assert "affidavit-verdict" in text
    assert COMMIT_A in text
    assert MANIFEST_A in text
    assert RUNNER_DIGEST in text
    assert CLAIM_ID in text
    assert "pass" in text
    assert "claim-other" in text
    assert "fail" in text
    assert "BEGIN SSH SIGNATURE" not in text

    ok, reason = mod.verify(
        signed,
        allow,
        expected_commit=COMMIT_A,
        expected_manifest_hash=MANIFEST_A,
    )
    assert ok is True, reason
    assert reason == ""


def test_verify_rejects_bad_signature(tmp_path: Path) -> None:
    """R2: verify rejects an attestation whose signature does not verify."""
    mod = _attestation()
    assert mod is not None, "affidavit.attestation must exist"
    key, blob = _generate_key(tmp_path)
    allow = _allowlist("ci", blob)
    signed = mod.emit(_verdict_body(), key_path=key)
    signed["signature"] = _corrupt(signed["signature"])
    ok, reason = mod.verify(
        signed,
        allow,
        expected_commit=COMMIT_A,
        expected_manifest_hash=MANIFEST_A,
    )
    assert ok is False
    assert reason == "bad signature"


def test_verify_rejects_tampered_payload(tmp_path: Path) -> None:
    """R2: changing bind fields after signing fails verify under the allowlist."""
    mod = _attestation()
    assert mod is not None, "affidavit.attestation must exist"
    key, blob = _generate_key(tmp_path)
    allow = _allowlist("ci", blob)
    signed = mod.emit(_verdict_body(), key_path=key)
    signed["claims"] = [{"id": CLAIM_ID, "result": "fail"}]
    ok, reason = mod.verify(
        signed,
        allow,
        expected_commit=COMMIT_A,
        expected_manifest_hash=MANIFEST_A,
    )
    assert ok is False
    assert reason == "bad signature"


def test_verify_rejects_wrong_commit(tmp_path: Path) -> None:
    """R3: a well-signed attestation for commit A fails when checked as B."""
    mod = _attestation()
    assert mod is not None, "affidavit.attestation must exist"
    key, blob = _generate_key(tmp_path)
    allow = _allowlist("ci", blob)
    signed = mod.emit(_verdict_body(commit=COMMIT_A), key_path=key)
    ok, reason = mod.verify(
        signed,
        allow,
        expected_commit=COMMIT_B,
        expected_manifest_hash=MANIFEST_A,
    )
    assert ok is False
    assert "commit" in reason


def test_verify_rejects_bind_mismatch_on_manifest_hash(tmp_path: Path) -> None:
    """R3: a well-signed attestation fails when the presented manifest hash differs."""
    mod = _attestation()
    assert mod is not None, "affidavit.attestation must exist"
    key, blob = _generate_key(tmp_path)
    allow = _allowlist("ci", blob)
    signed = mod.emit(
        _verdict_body(manifest_hash=MANIFEST_A),
        key_path=key,
    )
    ok, reason = mod.verify(
        signed,
        allow,
        expected_commit=COMMIT_A,
        expected_manifest_hash=MANIFEST_B,
    )
    assert ok is False
    assert "manifest" in reason


def test_ci_workflow_runs_verdict_and_attest() -> None:
    """R4: workflow must run an explicit fixture-build step and ship templates —
    not merely contain the strings verdict and attest."""
    workflows = REPO_ROOT / ".github" / "workflows"
    assert workflows.is_dir(), "expected .github/workflows"
    files = sorted(workflows.glob("*.yml")) + sorted(workflows.glob("*.yaml"))
    assert files, "expected at least one workflow file"
    text = "\n".join(path.read_text() for path in files)
    assert "verdict" in text, "workflow must run aff verdict"
    assert "attest" in text, "workflow must invoke the attest emit path"
    assert "build_verdict_repo" in text, (
        "workflow must invoke an explicit fixture builder (build_verdict_repo) "
        "before aff verdict"
    )

    builder = REPO_ROOT / "tests" / "fixtures" / "build_verdict_repo.sh"
    assert builder.is_file(), f"expected builder script at {builder}"

    fixture_root = REPO_ROOT / "tests" / "fixtures" / "verdict-repo"
    templates = (
        fixture_root / "app.py",
        fixture_root / "tests" / "test_widget.py",
        fixture_root / ".affidavit" / "manifest.json",
    )
    for path in templates:
        assert path.is_file(), f"expected tracked fixture template at {path}"
    gitignore = (REPO_ROOT / ".gitignore").read_text()
    assert "verdict-repo/.git" in gitignore, (
        "parent .gitignore must ignore the built nested .git under verdict-repo"
    )
    manifest = (fixture_root / ".affidavit" / "manifest.json").read_text()
    assert "claim-widget" in manifest, (
        "fixture manifest must declare claim-widget"
    )
