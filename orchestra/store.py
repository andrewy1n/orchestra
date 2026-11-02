"""Open the artifact store and read or write records through the library."""

from __future__ import annotations

import os
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError, open_store
from orchestra.canon.types import JsonObject, Record
from orchestra.canon.validation import ValidationError

__all__ = [
    "StoreBindingError",
    "create_record",
    "find_store_root",
    "get_record",
    "resolve_store",
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


def resolve_store(store: str | None, cwd: Path) -> Path:
    """Return the store root: the flag, then $ORCHESTRA_STORE, then the root found from cwd."""
    if store:
        return Path(store).expanduser()
    env = os.environ.get("ORCHESTRA_STORE")
    if env:
        return Path(env).expanduser()
    return find_store_root(cwd)


def get_record(root: Path, record_id: str, record_type: str | None = None) -> Record:
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
    payload: JsonObject,
    body: str | None = None,
) -> Record:
    project = open_store(root)
    try:
        return project.create(
            record_type=record_type,
            subject=subject,
            payload=payload,
            body=body,
        )
    except (StoreError, ValidationError) as exc:
        raise RuntimeError(str(exc)) from exc
