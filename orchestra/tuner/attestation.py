"""SSH-signed verdict attestations (namespace tuner-verdict)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from orchestra.tuner.sign import sign
from orchestra.tuner.sign import verify as verify_signed

NAMESPACE = "tuner-verdict"


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
    signed["signature"] = sign(NAMESPACE, payload, key_path)
    return signed


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
    if not verify_signed(NAMESPACE, canonical_payload(attestation), signature, allowlist_bytes):
        return False, "bad signature"
    return True, ""
