"""Typed reads of the artifact store for the dashboard backend."""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Generator, Mapping
from dataclasses import dataclass

from orchestra.canon.derive import attach_derived_all
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import Record


class ModelError(RuntimeError):
    pass


@dataclass(frozen=True)
class Catalog:
    key: str
    token: str
    records: list[Record]
    by_type: dict[str, list[Record]]


_catalog_lock = threading.Lock()
_catalog_cache: dict[str, Catalog] = {}
_pin = threading.local()


def change_token(target: Project) -> str:
    """Return the store's opaque record-change token."""
    return target.change_token()


def current_token(target: Project) -> str:
    """Return the pinned token, or read the store's change token when none is pinned."""
    pinned: str | None = getattr(_pin, "token", None)
    return pinned or change_token(target)


def pinned_catalog() -> Catalog | None:
    return getattr(_pin, "catalog", None)


@contextlib.contextmanager
def pinned_token(token: str) -> Generator[None, None, None]:
    previous_token: str | None = getattr(_pin, "token", None)
    previous_catalog = pinned_catalog()
    _pin.token = token
    if previous_catalog is not None and previous_catalog.token != token:
        _pin.catalog = None
    try:
        yield
    finally:
        _pin.token = previous_token
        _pin.catalog = previous_catalog


@contextlib.contextmanager
def pinned(catalog: Catalog) -> Generator[None, None, None]:
    previous_token: str | None = getattr(_pin, "token", None)
    previous_catalog = pinned_catalog()
    _pin.token = catalog.token
    _pin.catalog = catalog
    try:
        yield
    finally:
        _pin.token = previous_token
        _pin.catalog = previous_catalog


def load_catalog(target: Project, token: str) -> Catalog:
    """Read the store's catalog at this token. Raises ModelError on a failed read."""
    key = str(target.store_path)
    with _catalog_lock:
        cached = _catalog_cache.get(key)
        if cached and cached.token == token:
            return cached
        try:
            records = target.records()
            rows = attach_derived_all(records, target.derived(records))
        except (StoreError, OSError, ValueError) as exc:
            raise ModelError(f"catalog read failed: {exc}") from exc
        by_type: dict[str, list[Record]] = {}
        for row in rows:
            by_type.setdefault(row["record_type"], []).append(row)
        catalog = Catalog(key, token, rows, by_type)
        _catalog_cache[key] = catalog
        return catalog


def _catalog_view(target: Project) -> Catalog:
    view = pinned_catalog()
    if view is not None and view.key == str(target.store_path):
        return view
    return load_catalog(target, current_token(target))


def _catalog(target: Project) -> list[Record]:
    return _catalog_view(target).records


def catalog_records(target: Project) -> list[Record]:
    return _catalog(target)


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
    catalog = _catalog_view(target)
    rows = list(catalog.by_type.get(record_type, ())) if record_type else catalog.records
    if state:
        rows = [row for row in rows if row.get("lifecycle_state") == state]
    if subject:
        rows = [row for row in rows if (row.get("subject") or "").startswith(subject)]
    for field, expected in (payload or {}).items():
        rows = [row for row in rows if (row.get("payload") or {}).get(field) == expected]
    return rows
