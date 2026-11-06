from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Literal, TypeGuard


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def parse_hashes(value: object) -> dict[str, str]:
    if not _is_list(value) or not value:
        raise ValueError("oracle_hashes must be a non-empty array")
    hashes: dict[str, str] = {}
    for entry in value:
        if not isinstance(entry, str) or not (
            match := re.fullmatch(r"(.+):(sha256:[0-9a-fA-F]{64})", entry)
        ):
            raise ValueError("invalid oracle_hashes entry")
        path, digest = match.groups()
        relative = PurePosixPath(path)
        if (
            relative.is_absolute()
            or relative.as_posix() != path
            or path == "."
            or ".." in relative.parts
            or "\\" in path
            or "\x00" in path
        ):
            raise ValueError("invalid oracle file path")
        if path in hashes:
            raise ValueError(f"duplicate oracle hash for {path!r}")
        hashes[path] = digest.lower()
    return hashes


def parse_freeze(payload: Mapping[str, object]) -> dict[str, str]:
    hashes = parse_hashes(payload.get("oracle_hashes"))
    nodes = payload.get("test_ids")
    if not _is_list(nodes) or not nodes:
        raise ValueError("test_ids must be a non-empty array")
    for node in nodes:
        if not isinstance(node, str):
            raise ValueError("invalid test id")
        path, _, test = node.partition("::")
        if not test.strip() or node != node.strip() or path not in hashes:
            raise ValueError(f"invalid or unfrozen test id {node!r}")
    return hashes


OraclePolicy = Literal["none", "frozen"]


def resolve_oracle_policy(
    payload: Mapping[str, object], phase_payload: Mapping[str, object] | None = None
) -> OraclePolicy:
    declared = payload.get("oracle_policy")
    inherited = phase_payload.get("oracle_policy") if phase_payload is not None else None
    for value in (declared, inherited):
        if value is not None and value not in ("none", "frozen"):
            raise ValueError(f"invalid oracle_policy {value!r}")
    metadata = "test_ids" in payload or "oracle_hashes" in payload
    policy = declared or ("frozen" if metadata else inherited) or "none"
    if policy == "none":
        if metadata:
            raise ValueError("oracle_policy none conflicts with freeze metadata")
        return "none"
    if payload.get("method") not in ("tdd", "check"):
        raise ValueError("frozen oracle policy requires method tdd or check")
    parse_freeze(payload)
    return "frozen"
