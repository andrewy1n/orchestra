"""Open one artifact store for a project directory."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from orchestra.canon.derive import compute_derived
from orchestra.canon.git_backend import run_git
from orchestra.canon.index import SUPERSEDED, RecordIndex
from orchestra.canon.record import base_record, now
from orchestra.canon.schema import SchemaError, SchemaSet, TypeDef
from orchestra.canon.store import Store, StoreError, StaleWriteError
from orchestra.canon.validation import (
    ValidationError,
    check_transition,
    reject_event_mutation,
    reject_supersede_via_update,
    validate_record,
    validate_store,
)

Location = Literal["local", "global"]
_LOCAL_BINDING = "store-binding.local.json"
_COMMITTED_BINDING = "store-binding.json"
_BINDING_VALUES = frozenset({"local", "global"})


class StoreBindingError(Exception):
    """The selected store is missing, unbound, or not a local/global binding."""


@dataclass(frozen=True)
class Binding:
    """The binding that won: a local or global place, and where that choice came from.

    `location` is "local" or "global" when the opened directory is that place,
    including an explicit path or CANON_STORE that resolves to one of them.
    An explicit directory that is neither place has `location` None.
    `source` is "argument", "CANON_STORE", the binding file path, or "default".
    """

    location: Location | None
    source: str


_CURRENT_REVISION = "@current"


@dataclass(frozen=True)
class Project:
    """A project root and the single store opened for it."""

    project_root: Path
    store_path: Path
    binding: Binding

    def schemas(self) -> SchemaSet:
        return self._session()[1]

    def get(self, record_id: str, record_type: str | None = None) -> dict[str, Any]:
        """Return the stored record. With no type, find the id across record types."""
        store, schemas = self._session()
        return _read_record(store, schemas, record_id, record_type)

    def list(self, record_type: str) -> list[dict[str, Any]]:
        """Return every stored record of this type."""
        store, schemas = self._session()
        return store.list_records(schemas.resolve_type(record_type))

    def records(self) -> list[dict[str, Any]]:
        """Return every stored record of every type."""
        store, _ = self._session()
        return list(store.iter_records())

    def derived(self, records: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
        """Return read-time values (`ready`, `wave`, `referenced_by`, `corrected`) by record id.

        Pass the full record list from `records()` to skip a second read of the store.
        """
        store, schemas = self._session()
        return compute_derived(list(store.iter_records()) if records is None else records, schemas)

    def resolve(self, record_type: str, subject: str) -> dict[str, Any]:
        """Return the latest record of the type with the subject."""
        store, schemas = self._session()
        resolved = schemas.resolve_type(record_type)
        found = RecordIndex(store.iter_records(resolved)).resolve_subject(resolved, subject)
        if found is None:
            raise StoreError(f"unknown record: no {resolved} with subject {subject!r}")
        return found

    def validate(self) -> list[str]:
        """Return every validation error in the store."""
        store, schemas = self._session()
        return validate_store(schemas, store_root=store.root)

    def create(
        self,
        *,
        record_type: str,
        subject: str,
        payload: dict[str, Any],
        body: str | None = None,
        time: Any = None,
        provenance: Any = None,
    ) -> dict[str, Any]:
        """Write one record and return the stored record, including id and revision."""
        store, schemas = self._session()
        return _create_record(
            store,
            schemas,
            record_type=record_type,
            subject=subject,
            payload=payload,
            body=body,
            time=time,
            provenance=provenance,
        )

    def update(
        self,
        record_id: str,
        *,
        record_type: str | None = None,
        transition: str | None = None,
        payload: dict[str, Any] | None = None,
        body: str | None = None,
        expected_revision: str | None = _CURRENT_REVISION,
    ) -> dict[str, Any]:
        """Move a record to a new state and merge payload and body changes into it."""
        store, schemas = self._session()
        op = {
            "id": record_id,
            "type": record_type,
            "transition": transition,
            "payload": payload,
            "body": body,
            "expected_revision": expected_revision,
        }
        return _update_record(store, schemas, op)

    def supersede(
        self,
        record_id: str,
        *,
        record_type: str | None = None,
        payload: dict[str, Any] | None = None,
        body: str | None = None,
        expected_revision: str | None = _CURRENT_REVISION,
    ) -> dict[str, Any]:
        """Write a successor under a new id. Returns `record` and `predecessor`."""
        store, schemas = self._session()
        op = {
            "id": record_id,
            "type": record_type,
            "payload": payload,
            "body": body,
            "expected_revision": expected_revision,
        }
        return _supersede_record(store, schemas, op)

    def correct(
        self,
        record_id: str,
        *,
        record_type: str | None = None,
        payload: dict[str, Any] | None = None,
        body: str | None = None,
        subject: str | None = None,
        expected_revision: str | None = None,
    ) -> dict[str, Any]:
        """Write a correcting successor of an event record. Returns `record` and `predecessor`."""
        store, schemas = self._session()
        op = {
            "id": record_id,
            "type": record_type,
            "payload": payload,
            "body": body,
            "subject": subject,
            "expected_revision": expected_revision,
        }
        return _correct_record(store, schemas, op)

    def apply(self, operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Write each operation and return each result.

        A bad operation is reported and later operations still run. Earlier
        writes are left in place.
        """
        store, schemas = self._session()
        results: list[dict[str, Any]] = []
        for index, op in enumerate(operations, start=1):
            try:
                result = _apply_operation(store, schemas, op)
            except (StoreError, ValidationError) as exc:
                verb = op.get("op") if isinstance(op, dict) else None
                result = {
                    "ok": False,
                    "op": verb,
                    "error": _apply_error_code(exc),
                    "message": str(exc),
                }
            result["line"] = index
            results.append(result)
        return results

    def _session(self) -> tuple[Store, SchemaSet]:
        store = Store(self.store_path)
        config = store.load_config()
        return store, SchemaSet.load(store.root, config)


def open_store(directory: str | Path, *, store: str | Path | None = None) -> Project:
    """Open one store for `directory`. The first match wins; nothing after it is read."""
    root = _project_root(directory)
    if store is not None:
        chosen = Path(store)
        return _open(root, chosen, Binding(_location(root, chosen), "argument"))

    if "CANON_STORE" in os.environ:
        chosen = Path(os.environ["CANON_STORE"])
        return _open(root, chosen, Binding(_location(root, chosen), "CANON_STORE"))

    bound = _binding_file(root)
    if bound is not None:
        path, kind = bound
        return _open(root, _place(root, kind), Binding(kind, str(path)))

    local = root / ".canon"
    if _has_config(local):
        return _open(root, local, Binding("local", "default"))

    home = _global_store(root)
    if _has_config(home):
        return _open(root, home, Binding("global", "default"))

    raise StoreBindingError(
        f"No artifact store for {root}: neither {local / 'config.json'} nor {home / 'config.json'} exists"
    )


def _project_root(directory: str | Path) -> Path:
    directory = Path(directory)
    try:
        proc = run_git(
            directory,
            "rev-parse",
            "--show-toplevel",
            capture_output=True,
            text=True,
        )
    except OSError:
        return directory.resolve()
    if proc.returncode != 0 or not proc.stdout.strip():
        return directory.resolve()
    return Path(proc.stdout.strip()).resolve()


def _global_store(root: Path) -> Path:
    return Path.home() / ".canon" / root.name


def _place(root: Path, kind: Location) -> Path:
    if kind == "local":
        return root / ".canon"
    return _global_store(root)


def _location(root: Path, store: Path) -> Location | None:
    resolved = store.resolve()
    if resolved == (root / ".canon").resolve():
        return "local"
    if resolved == _global_store(root).resolve():
        return "global"
    return None


def _has_config(store: Path) -> bool:
    return (store / "config.json").is_file()


def _binding_file(root: Path) -> tuple[Path, Location] | None:
    artifacts = root / ".canon"
    for name in (_LOCAL_BINDING, _COMMITTED_BINDING):
        path = artifacts / name
        if not path.exists():
            continue
        return path, _read_binding(path)
    return None


def _read_binding(path: Path) -> Location:
    source = str(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise StoreBindingError(f"Cannot read store binding {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise StoreBindingError(f"Invalid store binding JSON in {source}: {exc}") from exc
    if not isinstance(data, dict) or "store" not in data:
        raise StoreBindingError(
            f"Invalid store binding in {source}: expected an object with a store key"
        )
    value = data.get("store")
    if not isinstance(value, str) or value not in _BINDING_VALUES:
        raise StoreBindingError(
            f"Invalid store binding from {source}: expected \"local\" or \"global\", got {value!r}"
        )
    return value  # type: ignore[return-value]


def _open(root: Path, store: Path, binding: Binding) -> Project:
    if not _has_config(store):
        raise StoreBindingError(
            f"Store selected by {binding.source} at {store} has no config.json"
        )
    return Project(project_root=root, store_path=store.resolve(), binding=binding)


_OP_KEYS = {
    "create": {"op", "type", "subject", "payload", "body", "time", "provenance"},
    "update": {"op", "id", "type", "transition", "payload", "body", "expected_revision"},
    "supersede": {"op", "id", "type", "payload", "body", "expected_revision"},
    "correct": {"op", "id", "type", "subject", "payload", "body", "expected_revision"},
}


def _find_record_by_id(
    store: Store, schemas: SchemaSet, record_id: str
) -> dict[str, Any] | None:
    for record_type in schemas.types:
        if store.record_exists(record_type, record_id):
            return store.read_record(record_type, record_id)
    return None


def _read_record(
    store: Store, schemas: SchemaSet, record_id: str, type_arg: str | None
) -> dict[str, Any]:
    if type_arg is None:
        found = _find_record_by_id(store, schemas, record_id)
        if found is None:
            raise StoreError(f"unknown record: {record_id}")
        return found
    resolved = schemas.resolve_type(type_arg)
    try:
        return store.read_record(resolved, record_id)
    except StoreError as exc:
        if "unknown record" not in str(exc):
            raise
        other = _find_record_by_id(store, schemas, record_id)
        if other is not None and other.get("record_type") != resolved:
            raise StoreError(
                f"record {record_id} is {other['record_type']!r}, not {resolved!r}"
            ) from exc
        raise StoreError(f"unknown record: {record_id}") from exc


def _payload_object(payload: dict[str, Any] | None) -> dict[str, Any]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise StoreError("payload must be a JSON object")
    return dict(payload)


def _body_text(body: str | None) -> str:
    if body is None:
        return ""
    if not isinstance(body, str):
        raise StoreError("body must be a string")
    return body


def _persist_new(store: Store, type_def: TypeDef, record: dict[str, Any]) -> dict[str, Any]:
    stored = store.create_record(record)
    if type_def.lifecycle.appends_only:
        try:
            store.archive_history(stored)
        except Exception:
            store.delete_record_file(stored["record_type"], stored["id"])
            raise
    return stored


def _require_one_active(type_def: TypeDef, index: RecordIndex, record: dict[str, Any], ignore: str | None = None) -> None:
    if type_def.lifecycle.name != "current":
        return
    for other in index.by_subject.get((record["record_type"], record["subject"]), []):
        if other["id"] != ignore and other["lifecycle_state"] == type_def.lifecycle.initial:
            raise ValidationError(
                f"another active {record['record_type']} already exists for "
                f"subject={record['subject']!r}: supersede {other['id']}"
            )


def _create_record(
    store: Store,
    schemas: SchemaSet,
    *,
    record_type: str,
    subject: str | None,
    payload: dict[str, Any] | None,
    body: str | None = None,
    time: Any = None,
    provenance: Any = None,
) -> dict[str, Any]:
    resolved = schemas.resolve_type(record_type)
    type_def = schemas.types[resolved]
    if not isinstance(subject, str) or not subject:
        raise StoreError("missing subject")
    record = base_record(
        type_def,
        subject=subject,
        payload=_payload_object(payload),
        record_id=store.new_id(),
        body=_body_text(body),
        time=time,
        provenance=provenance,
    )
    index = RecordIndex(store.iter_records())
    _require_one_active(type_def, index, record)
    validate_record(schemas, record, index)
    return _persist_new(store, type_def, record)


def _read_for_update(
    store: Store, schemas: SchemaSet, op: dict[str, Any], *, verb: str
) -> dict[str, Any]:
    record_id = op.get("id")
    if not isinstance(record_id, str) or not record_id:
        raise StoreError(f"{verb} requires id")
    return _read_record(store, schemas, record_id, op.get("type") or None)


def _expected_revision(op: dict[str, Any], old: dict[str, Any]) -> str | None:
    raw = op["expected_revision"] if "expected_revision" in op else _CURRENT_REVISION
    if raw == _CURRENT_REVISION:
        return old["revision"]
    return raw


def _update_record(store: Store, schemas: SchemaSet, op: dict[str, Any]) -> dict[str, Any]:
    old = _read_for_update(store, schemas, op, verb="update")
    type_def = schemas.types[old["record_type"]]
    src = old["lifecycle_state"]
    transition = op.get("transition")
    dest = transition or src
    reject_event_mutation(type_def)
    if transition:
        reject_supersede_via_update(type_def, dest)
        check_transition(type_def, src, dest)
    record = dict(old)
    record["lifecycle_state"] = dest
    record["recorded_at"] = now()
    if op.get("body") is not None:
        record["body"] = _body_text(op.get("body"))
    payload_updates = op.get("payload") or {}
    if payload_updates:
        if not isinstance(payload_updates, dict):
            raise StoreError("payload must be a JSON object")
        record["payload"] = {**(record.get("payload") or {}), **payload_updates}
    validate_record(schemas, record, RecordIndex(store.iter_records()))
    return store.write_record(
        record, expected_revision=_expected_revision(op, old), archive_prior=old
    )


def _carried_body(op: dict[str, Any], old: dict[str, Any]) -> str:
    if op.get("body") is None:
        return old.get("body") or ""
    return _body_text(op.get("body"))


def _successor_payload(op: dict[str, Any], old: dict[str, Any]) -> dict[str, Any]:
    return {**(old.get("payload") or {}), **_payload_object(op.get("payload"))}


def _supersede_record(store: Store, schemas: SchemaSet, op: dict[str, Any]) -> dict[str, Any]:
    old = _read_for_update(store, schemas, op, verb="supersede")
    type_def = schemas.types[old["record_type"]]
    reject_event_mutation(type_def)
    check_transition(type_def, old["lifecycle_state"], SUPERSEDED)
    stamp = now()
    successor = base_record(
        type_def,
        subject=old["subject"],
        payload=_successor_payload(op, old),
        record_id=store.new_id(),
        relationships={"supersedes": [old["id"]]},
        body=_carried_body(op, old),
        time=old.get("time"),
        provenance=old.get("provenance"),
        recorded_at=stamp,
    )
    index = RecordIndex(store.iter_records())
    _require_one_active(type_def, index, successor, ignore=old["id"])
    validate_record(schemas, successor, index)
    old_updated = dict(old)
    old_updated["lifecycle_state"] = SUPERSEDED
    old_updated["recorded_at"] = stamp
    predecessor = store.write_record(
        old_updated, expected_revision=_expected_revision(op, old), archive_prior=old
    )
    stored = store.create_record(successor)
    return {"ok": True, "op": "supersede", "record": stored, "predecessor": predecessor}


def _correct_record(store: Store, schemas: SchemaSet, op: dict[str, Any]) -> dict[str, Any]:
    old = _read_for_update(store, schemas, op, verb="correct")
    if "expected_revision" in op and op["expected_revision"] is not None:
        expected = _expected_revision(op, old)
        if expected != old["revision"]:
            raise StaleWriteError(f"expected {expected}, found {old['revision']}")
    type_def = schemas.types[old["record_type"]]
    if not type_def.lifecycle.appends_only:
        raise ValidationError(
            f"{old['record_type']} does not use successor-record correction", "not_correctable"
        )
    index = RecordIndex(store.iter_records())
    if old["id"] in index.corrected:
        raise ValidationError(f"{old['id']} is already corrected; correct the latest record")
    successor = base_record(
        type_def,
        subject=op.get("subject") or old["subject"],
        payload=_successor_payload(op, old),
        record_id=store.new_id(),
        relationships={"corrects": [old["id"]]},
        body=_carried_body(op, old),
        time=old.get("time"),
        provenance=old.get("provenance"),
    )
    validate_record(schemas, successor, index)
    stored = _persist_new(store, type_def, successor)
    return {"ok": True, "op": "correct", "record": stored, "predecessor": old}


def _apply_operation(store: Store, schemas: SchemaSet, op: Any) -> dict[str, Any]:
    if not isinstance(op, dict):
        raise StoreError("operation must be an object")
    verb = op.get("op")
    if verb not in _OP_KEYS:
        raise StoreError(f"unsupported op {verb!r}; expected one of {list(_OP_KEYS)}")
    unknown = sorted(set(op) - _OP_KEYS[verb])
    if unknown:
        raise StoreError(f"{verb} does not take {unknown}")
    if verb == "create":
        stored = _create_record(
            store,
            schemas,
            record_type=cast(str, op.get("type")),
            subject=op.get("subject"),
            payload=op.get("payload"),
            body=op.get("body"),
            time=op.get("time"),
            provenance=op.get("provenance"),
        )
        return {"ok": True, "op": "create", "record": stored}
    if verb == "update":
        return {"ok": True, "op": "update", "record": _update_record(store, schemas, op)}
    if verb == "supersede":
        return _supersede_record(store, schemas, op)
    return _correct_record(store, schemas, op)


def _apply_error_code(exc: Exception) -> str:
    if isinstance(exc, StaleWriteError):
        return "stale_write"
    if isinstance(exc, ValidationError):
        return "validation"
    if isinstance(exc, SchemaError):
        return "schema"
    message = str(exc)
    if message.startswith("unknown record type") or message.startswith("unsafe record type"):
        return "unknown_type"
    if message.startswith("unknown record"):
        return "not_found"
    if message.startswith("unsupported op"):
        return "unknown_op"
    if message.startswith("ambiguous record type"):
        return "ambiguous_type"
    return "store"
