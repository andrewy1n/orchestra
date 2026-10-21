"""Open the artifact store and read or write records through the library."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adaptive_artifacts.contract import ContractError
from adaptive_artifacts.project import StoreBindingError, open_store
from adaptive_artifacts.store import StoreError
from adaptive_artifacts.validation import ValidationError

__all__ = [
    "StoreBindingError",
    "find_store_root",
    "get_record",
    "create_record",
]


def find_store_root(start: Path) -> Path:
    """Walk up from start for a project root that opens a store."""
    cur = start.resolve()
    for candidate in [cur, *cur.parents]:
        try:
            project = open_store(candidate)
        except StoreBindingError:
            continue
        return project.project_root
    return start.resolve()


def get_record(root: Path, record_id: str, record_type: str | None = None) -> dict[str, Any]:
    project = open_store(root)
    try:
        return project.get(record_id, record_type)
    except StoreError as exc:
        raise LookupError(str(exc)) from exc


def create_record(
    root: Path,
    *,
    record_type: str,
    subject: str,
    payload: dict[str, Any],
    rels: list[str] | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    project = open_store(root)
    try:
        return project.create(
            record_type=record_type,
            subject=subject,
            payload=payload,
            rels=rels,
            body=body,
        )
    except (StoreError, ContractError, ValidationError) as exc:
        raise RuntimeError(str(exc)) from exc
