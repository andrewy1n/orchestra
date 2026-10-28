"""Allowlist-signed human claims as a witness in place of red-green tests."""

from __future__ import annotations

from orchestra.tuner.sign import verify

NAMESPACE = "tuner-claim"


def canonical_payload(claim_id: str, text: str) -> bytes:
    """UTF-8 bytes a human signs for one claim."""
    return f"tuner-claim v1\nclaim: {claim_id}\ntext: {text}\n".encode("utf-8")


def verify_claim_signature(
    claim_id: str,
    text: str,
    signature: str,
    allowlist_bytes: bytes,
) -> bool:
    """True when any allowlist principal verifies the claim payload."""
    if not signature:
        return False
    return verify(
        NAMESPACE,
        canonical_payload(claim_id, text),
        signature,
        allowlist_bytes,
    )
