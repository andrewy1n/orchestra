"""Sign and verify payload bytes in an allowlist namespace."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def sign(namespace: str, payload: bytes, key_path: Path | str) -> str:
    """Return the signature text for payload bytes in namespace."""
    completed = subprocess.run(
        [
            "ssh-keygen",
            "-Y",
            "sign",
            "-f",
            str(key_path),
            "-n",
            namespace,
        ],
        input=payload,
        check=True,
        capture_output=True,
    )
    return completed.stdout.decode("utf-8")


def verify(
    namespace: str,
    payload: bytes,
    signature: str | bytes,
    allowlist_bytes: bytes,
) -> bool:
    """True when any allowlist principal verifies payload in namespace."""
    principals = _principals(allowlist_bytes)
    if not principals:
        return False
    sig_bytes = signature.encode("utf-8") if isinstance(signature, str) else bytes(signature)
    if not sig_bytes:
        return False
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        allowlist_path = directory / "allowed_signers"
        sig_path = directory / "payload.sig"
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
                    namespace,
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
