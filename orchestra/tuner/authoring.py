"""Standalone claim authoring: append claims and freeze oracle hashes."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import TypeAlias

from orchestra.canon.types import JsonObject, JsonValue
from orchestra.tuner.manifest import MANIFEST_PATH

_JsonKey: TypeAlias = str | int | float | bool | None


class AuthoringError(Exception):
    """The requested manifest edit is invalid; the manifest is left unchanged."""


def add_claim(
    cwd: Path | str,
    claim_id: str,
    text: str,
    tests: Sequence[str],
) -> None:
    """Append a claim with empty ``oracle_hashes``, creating the manifest if absent."""
    path = Path(cwd) / MANIFEST_PATH
    document: JsonObject = _read(path) if path.exists() else {"claims": [], "amendments": []}
    claims = document.setdefault("claims", [])
    if not isinstance(claims, list):
        raise AuthoringError("manifest claims must be a list")
    if any(isinstance(c, dict) and c.get("id") == claim_id for c in claims):
        raise AuthoringError(f"duplicate claim id {claim_id!r}")
    claims.append(
        {
            "id": claim_id,
            "text": text,
            "tests": list(tests),
            "oracle_hashes": {},
        }
    )
    _write(path, document)


def freeze(cwd: Path | str, claim_ids: Sequence[str] = ()) -> None:
    """Set ``oracle_hashes`` from working-tree files for the named claims (default all)."""
    root = Path(cwd)
    path = root / MANIFEST_PATH
    if not path.exists():
        raise AuthoringError(f"missing {MANIFEST_PATH}")
    document = _read(path)
    claims = document.get("claims")
    if not isinstance(claims, list):
        raise AuthoringError("manifest claims must be a list")
    by_id: dict[_JsonKey, JsonObject] = {}
    for claim in claims:
        if isinstance(claim, dict):
            by_id[_json_key(claim.get("id"))] = claim
    selected: list[_JsonKey] = (
        [_json_key(claim_id) for claim_id in claim_ids] if claim_ids else list(by_id)
    )
    for claim_id in selected:
        if claim_id not in by_id:
            raise AuthoringError(f"unknown claim id {claim_id!r}")

    global_support = _support_list(document.get("support_files"), "support_files")
    updates: dict[_JsonKey, JsonObject] = {}
    for claim_id in selected:
        claim = by_id[claim_id]
        for relpath in (
            *global_support,
            *_support_list(claim.get("support_files"), f"{claim_id} support_files"),
        ):
            _hash_file(root, relpath)
        hashes: JsonObject = {}
        raw_tests = claim.get("tests") or []
        if isinstance(raw_tests, list):
            nodes: Sequence[JsonValue] = raw_tests
        elif isinstance(raw_tests, (dict, str)):
            nodes = list(raw_tests)
        else:
            raise TypeError(f"'{type(raw_tests).__name__}' object is not iterable")
        for node in nodes:
            relpath = str(node).split("::", 1)[0]
            if relpath not in hashes:
                hashes[relpath] = _hash_file(root, relpath)
        updates[claim_id] = hashes

    for claim_id, hashes in updates.items():
        by_id[claim_id]["oracle_hashes"] = hashes
    _write(path, document)


def _support_list(value: JsonValue, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise AuthoringError(f"{label} must be a list of paths")
    return [item for item in value if isinstance(item, str)]


def _json_key(value: JsonValue) -> _JsonKey:
    if isinstance(value, (dict, list)):
        kind = "dict" if isinstance(value, dict) else "list"
        raise TypeError(f"unhashable type: '{kind}'")
    return value


def _hash_file(root: Path, relpath: str) -> str:
    target = root / relpath
    if not target.is_file():
        raise AuthoringError(f"missing file {relpath}")
    return "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()


def _read(path: Path) -> JsonObject:
    try:
        document: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuthoringError(f"invalid JSON in {MANIFEST_PATH}") from exc
    if not isinstance(document, dict):
        raise AuthoringError("manifest must be a JSON object")
    return document


def _write(path: Path, document: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
