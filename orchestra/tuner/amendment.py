"""Signed amendment chains for claim test-id and hash changes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from orchestra.canon.types import JsonValue
from orchestra.tuner.sign import verify as verify_signed


def canonical_payload(amendment: Mapping[str, JsonValue]) -> bytes:
    """UTF-8 bytes signed for one amendment. The signature field is omitted.

    ``old_support_hashes`` / ``new_support_hashes`` and ``old_runner_digest`` /
    ``new_runner_digest`` are included only when present so existing
    test/hash-only amendments keep the same signed bytes.
    """
    lines = [
        "tuner-amendment v1",
        f"claim: {amendment['claim']}",
        "old_tests: " + ",".join(_string_list(amendment["old_tests"])),
        "new_tests: " + ",".join(_string_list(amendment["new_tests"])),
        "old_hashes:",
    ]
    old_hashes = _string_mapping(amendment["old_hashes"])
    new_hashes = _string_mapping(amendment["new_hashes"])
    for relpath in sorted(old_hashes):
        lines.append(f"{relpath} {old_hashes[relpath]}")
    lines.append("new_hashes:")
    for relpath in sorted(new_hashes):
        lines.append(f"{relpath} {new_hashes[relpath]}")
    if "old_support_hashes" in amendment or "new_support_hashes" in amendment:
        old_support = _string_mapping(amendment.get("old_support_hashes") or {})
        new_support = _string_mapping(amendment.get("new_support_hashes") or {})
        lines.append("old_support_hashes:")
        for relpath in sorted(old_support):
            lines.append(f"{relpath} {old_support[relpath]}")
        lines.append("new_support_hashes:")
        for relpath in sorted(new_support):
            lines.append(f"{relpath} {new_support[relpath]}")
    if "old_runner_digest" in amendment or "new_runner_digest" in amendment:
        lines.append(f"old_runner_digest: {amendment.get('old_runner_digest', '')}")
        lines.append(f"new_runner_digest: {amendment.get('new_runner_digest', '')}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def verify_signature(
    payload: bytes,
    signature: str | bytes,
    allowlist_bytes: bytes,
) -> bool:
    """True when any allowlist principal verifies the payload."""
    return verify_signed("tuner-amendment", payload, signature, allowlist_bytes)


def _as_tests(value: JsonValue) -> list[str]:
    return list(_string_list(value))


def _as_hashes(value: JsonValue) -> dict[str, str]:
    return dict(_string_mapping(value or {}))


def _string_list(value: JsonValue) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError("expected a list of strings")
    return [item for item in value if isinstance(item, str)]


def _string_mapping(value: JsonValue) -> dict[str, str]:
    if not isinstance(value, dict) or not all(isinstance(item, str) for item in value.values()):
        raise TypeError("expected a string mapping")
    return {key: item for key, item in value.items() if isinstance(item, str)}


def _as_runner_digest(value: JsonValue) -> str:
    if value is None:
        return ""
    return str(value)


def authorize(
    base_claim: Mapping[str, JsonValue],
    head_claim: Mapping[str, JsonValue],
    amendments: Sequence[Mapping[str, JsonValue]],
    base_allowlist: bytes,
    head_allowlist: bytes,
) -> tuple[bool, str]:
    """Whether amendments connect base to head under the base allowlist.

    Support hashes and runner digests chain like oracle hashes. Omitted
    amendment fields leave that dimension unchanged (back-compat with
    test/hash-only steps). Absent claim fields mean empty / no digest.
    """
    if base_allowlist != head_allowlist:
        return False, "allowlist changed"
    current_tests = _as_tests(base_claim["tests"])
    current_hashes = _as_hashes(base_claim["oracle_hashes"])
    current_support = _as_hashes(base_claim.get("support_hashes"))
    current_runner = _as_runner_digest(base_claim.get("runner_digest"))
    head_tests = _as_tests(head_claim["tests"])
    head_hashes = _as_hashes(head_claim["oracle_hashes"])
    head_support = _as_hashes(head_claim.get("support_hashes"))
    head_runner = _as_runner_digest(head_claim.get("runner_digest"))
    if (
        current_tests == head_tests
        and current_hashes == head_hashes
        and current_support == head_support
        and current_runner == head_runner
    ):
        return True, ""
    claim_id = base_claim["id"]
    for amendment in amendments:
        if amendment.get("claim") != claim_id:
            continue
        old_tests = _as_tests(amendment["old_tests"])
        old_hashes = _as_hashes(amendment["old_hashes"])
        if old_tests != current_tests or old_hashes != current_hashes:
            return False, "missing step"
        touches_support = "old_support_hashes" in amendment or "new_support_hashes" in amendment
        if touches_support:
            old_support = _as_hashes(amendment.get("old_support_hashes"))
            if old_support != current_support:
                return False, "missing step"
        touches_runner = "old_runner_digest" in amendment or "new_runner_digest" in amendment
        if touches_runner:
            old_runner = _as_runner_digest(amendment.get("old_runner_digest"))
            if old_runner != current_runner:
                return False, "missing step"
        signature = amendment.get("signature", b"")
        if not isinstance(signature, (str, bytes)):
            return False, "bad signature"
        if not verify_signature(canonical_payload(amendment), signature, base_allowlist):
            return False, "bad signature"
        current_tests = _as_tests(amendment["new_tests"])
        current_hashes = _as_hashes(amendment["new_hashes"])
        if touches_support:
            current_support = _as_hashes(amendment.get("new_support_hashes"))
        if touches_runner:
            current_runner = _as_runner_digest(amendment.get("new_runner_digest"))
    if (
        current_tests != head_tests
        or current_hashes != head_hashes
        or current_support != head_support
        or current_runner != head_runner
    ):
        return False, "missing step"
    return True, ""
