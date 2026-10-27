"""Allowlist-signed human claims as a witness in place of red-green tests."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from affidavit.amendment import _principals

NAMESPACE = "affidavit-claim"


def canonical_payload(claim_id: str, text: str) -> bytes:
    """UTF-8 bytes a human signs for one claim."""
    return f"affidavit-claim v1\nclaim: {claim_id}\ntext: {text}\n".encode("utf-8")


def verify_claim_signature(
    claim_id: str,
    text: str,
    signature: str,
    allowlist_bytes: bytes,
) -> bool:
    """True when any allowlist principal verifies the claim payload."""
    principals = _principals(allowlist_bytes)
    if not principals or not signature:
        return False
    payload = canonical_payload(claim_id, text)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        allowlist_path = directory / "allowed_signers"
        sig_path = directory / "claim.sig"
        allowlist_path.write_bytes(allowlist_bytes)
        sig_path.write_bytes(signature.encode("utf-8"))
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
