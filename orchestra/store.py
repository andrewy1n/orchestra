"""Open the artifact store and read or write records through the library."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project, StoreBindingError, bound_store_path, open_store
from orchestra.canon.types import JsonObject, Record
from orchestra.canon.validation import ValidationError

__all__ = [
    "StoreBindingError",
    "StoreLocation",
    "create_record",
    "find_store_root",
    "get_record",
    "resolve_location",
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


@dataclass(frozen=True)
class StoreLocation:
    root: Path
    store: Path | None

    def open(self) -> Project:
        return open_store(self.root, store=self.store)


def resolve_location(store: str | None, cwd: Path) -> StoreLocation:
    """Resolve the root; an explicit flag or $ORCHESTRA_STORE also pins the store its binding names."""
    root = resolve_store(store, cwd)
    explicit = bool(store or os.environ.get("ORCHESTRA_STORE"))
    return StoreLocation(root, bound_store_path(root) if explicit else None)


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
