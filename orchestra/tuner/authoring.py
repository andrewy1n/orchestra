"""Standalone claim authoring: append claims and freeze oracle hashes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

from affidavit.manifest import MANIFEST_PATH


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
    document = _read(path) if path.exists() else {"claims": [], "amendments": []}
    claims = document.setdefault("claims", [])
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
    by_id = {c.get("id"): c for c in claims if isinstance(c, dict)}
    selected = list(claim_ids) if claim_ids else [c.get("id") for c in claims if isinstance(c, dict)]
    for claim_id in selected:
        if claim_id not in by_id:
            raise AuthoringError(f"unknown claim id {claim_id!r}")

    global_support = _support_list(document.get("support_files"), "support_files")
    updates: dict[str, dict[str, str]] = {}
    for claim_id in selected:
        claim = by_id[claim_id]
        for relpath in (
            *global_support,
            *_support_list(claim.get("support_files"), f"{claim_id} support_files"),
        ):
            _hash_file(root, relpath)
        hashes: dict[str, str] = {}
        for node in claim.get("tests") or []:
            relpath = str(node).split("::", 1)[0]
            if relpath not in hashes:
                hashes[relpath] = _hash_file(root, relpath)
        updates[claim_id] = hashes

    for claim_id, hashes in updates.items():
        by_id[claim_id]["oracle_hashes"] = hashes
    _write(path, document)


def _support_list(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise AuthoringError(f"{label} must be a list of paths")
    return value


def _hash_file(root: Path, relpath: str) -> str:
    target = root / relpath
    if not target.is_file():
        raise AuthoringError(f"missing file {relpath}")
    return "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()


def _read(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuthoringError(f"invalid JSON in {MANIFEST_PATH}") from exc
    if not isinstance(document, dict):
        raise AuthoringError("manifest must be a JSON object")
    return document


def _write(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
