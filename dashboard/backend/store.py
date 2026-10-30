"""Typed reads of the artifact store for the dashboard backend."""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Iterator, Mapping
from typing import Any

from orchestra.canon.derive import attach_derived_all
from orchestra.canon.project import Project
from orchestra.canon.store import StoreError

Record = dict[str, Any]


class ModelError(RuntimeError):
    pass


_catalog_lock = threading.Lock()
_catalog_cache: dict[str, tuple[str, list[Record]]] = {}
_pin = threading.local()


def change_token(target: Project) -> str:
    """Return the store's opaque record-change token."""
    return target.change_token()


@contextlib.contextmanager
def pinned_token(token: str) -> Iterator[None]:
    _pin.token = token
    try:
        yield
    finally:
        _pin.token = None


def _catalog(target: Project) -> list[Record]:
    key = str(target.store_path)
    with _catalog_lock:
        token = getattr(_pin, "token", None) or change_token(target)
        cached = _catalog_cache.get(key)
        if cached and cached[0] == token:
            return cached[1]
        try:
            records = target.records()
            rows = attach_derived_all(records, target.derived(records))
        except StoreError:
            return []
        _catalog_cache[key] = (token, rows)
        return rows


def declared_record_types(target: Project) -> frozenset[str] | None:
    """Record type ids from the store's schema snapshots, or None if unreadable."""
    try:
        return frozenset(target.schemas().types)
    except (StoreError, OSError, ValueError):
        return None


def stored_record(target: Project, record_id: str, record_type: str | None = None) -> Record:
    """Return the record as stored, without derived values. Raises StoreError."""
    return target.get(record_id, record_type)


def get_record(target: Project, record_id: str, record_type: str | None = None) -> Record:
    """Return one record with its derived values attached."""
    try:
        record = stored_record(target, record_id, record_type)
    except (StoreError, OSError, ValueError) as exc:
        label = f"get --type {record_type}" if record_type else f"get --id {record_id}"
        raise ModelError(f"{label} failed: {exc}") from exc
    derived = next((row for row in _catalog(target) if row.get("id") == record_id), None)
    return derived or record


def list_records(
    target: Project,
    record_type: str | None = None,
    *,
    state: str | None = None,
    subject: str | None = None,
    payload: Mapping[str, str] | None = None,
) -> list[Record]:
    """Return catalog records, filtered by type, lifecycle state, subject prefix, and payload fields."""
    try:
        rows = _catalog(target)
    except (OSError, ValueError) as exc:
        label = f"list --type {record_type}" if record_type else f"list --subject {subject}"
        raise ModelError(f"{label} failed: {exc}") from exc
    if record_type:
        rows = [row for row in rows if row.get("record_type") == record_type]
    if state:
        rows = [row for row in rows if row.get("lifecycle_state") == state]
    if subject:
        rows = [row for row in rows if (row.get("subject") or "").startswith(subject)]
    for field, expected in (payload or {}).items():
        rows = [row for row in rows if (row.get("payload") or {}).get(field) == expected]
    return rows
