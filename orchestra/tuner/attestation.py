"""SSH-signed verdict attestations (namespace affidavit-verdict)."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping

NAMESPACE = "affidavit-verdict"


def canonical_payload(attestation: Mapping[str, Any]) -> bytes:
    """UTF-8 bytes signed for one attestation. The signature field is omitted."""
    lines = [
        f"{NAMESPACE} v1",
        f"commit: {attestation['commit']}",
        f"manifest_hash: {attestation['manifest_hash']}",
        f"runner_digest: {attestation['runner_digest']}",
        "claims:",
    ]
    for claim in attestation["claims"]:
        lines.append(f"{claim['id']} {claim['result']}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def emit(body: Mapping[str, Any], *, key_path: Path | str) -> dict[str, Any]:
    """Sign a verdict body and return an attestation dict with a signature."""
    signed: dict[str, Any] = {
        "commit": body["commit"],
        "manifest_hash": body["manifest_hash"],
        "runner_digest": body["runner_digest"],
        "claims": list(body["claims"]),
    }
    payload = canonical_payload(signed)
    completed = subprocess.run(
        [
            "ssh-keygen",
            "-Y",
            "sign",
            "-f",
            str(key_path),
            "-n",
            NAMESPACE,
        ],
        input=payload,
        check=True,
        capture_output=True,
    )
    signed["signature"] = completed.stdout.decode("utf-8")
    return signed


def _principals(allowlist_bytes: bytes) -> list[str]:
    try:
        text = allowlist_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return []
    principals: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        principals.append(stripped.split()[0])
    return principals


def _verify_signature(
    payload: bytes,
    signature: str | bytes,
    allowlist_bytes: bytes,
) -> bool:
    principals = _principals(allowlist_bytes)
    if not principals:
        return False
    sig_bytes = signature.encode("utf-8") if isinstance(signature, str) else bytes(signature)
    if not sig_bytes:
        return False
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        allowlist_path = directory / "allowed_signers"
        sig_path = directory / "attestation.sig"
        allowlist_path.write_bytes(allowlist_bytes)
        sig_path.write_bytes(sig_bytes)
        for principal in principals:
            completed = subprocess.run(
                [
                    "ssh-keygen",
                    "-Y",
                    "verify",
                    "-f",
                    str(allowlist_path),
                    "-I",
                    principal,
                    "-n",
                    NAMESPACE,
                    "-s",
                    str(sig_path),
                ],
                input=payload,
                capture_output=True,
                check=False,
            )
            if completed.returncode == 0:
                return True
    return False


def verify(
    attestation: Mapping[str, Any],
    allowlist_bytes: bytes,
    *,
    expected_commit: str,
    expected_manifest_hash: str,
) -> tuple[bool, str]:
    """Whether the attestation verifies under the allowlist and bind fields."""
    if attestation.get("commit") != expected_commit:
        return False, "commit mismatch"
    if attestation.get("manifest_hash") != expected_manifest_hash:
        return False, "manifest mismatch"
    signature = attestation.get("signature", "")
    if not _verify_signature(canonical_payload(attestation), signature, allowlist_bytes):
        return False, "bad signature"
    return True, ""
