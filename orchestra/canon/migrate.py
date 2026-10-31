"""Declarative schema migrations over the records and history of a store."""

from __future__ import annotations

from orchestra.canon.backend import Backend
from orchestra.canon.record import prepare_record
from orchestra.canon.revision import with_revision
from orchestra.canon.schema import SchemaError
from orchestra.canon.types import JsonObject, JsonValue, Record


def migration_path(module: JsonObject, old_major: int, new_major: int) -> list[JsonObject]:
    migrations = module.get("migrations") or []
    steps: dict[int, JsonObject] = {}
    if isinstance(migrations, list):
        for step in migrations:
            if isinstance(step, dict):
                start = step.get("from")
                if isinstance(start, str):
                    steps[int(start)] = step
    path: list[JsonObject] = []
    current = old_major
    while current < new_major:
        step = steps.get(current)
        if step is None:
            raise SchemaError(
                f"{module['namespace']}: no migration from major {current} toward {new_major}"
            )
        target = step.get("to")
        if not isinstance(target, str):
            raise TypeError("migration target must be a string")
        if int(target) > new_major:
            raise SchemaError(
                f"{module['namespace']}: no migration from major {current} toward {new_major}"
            )
        path.append(step)
        current = int(target)
    return path


def _map_value(mapping: dict[str, JsonValue], value: JsonValue) -> JsonValue:
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [_map_value(mapping, item) for item in value]
    return value


def transform(record: Record, steps: list[JsonObject]) -> Record:
    out: Record = record.copy()
    payload = dict(record["payload"])
    for step in steps:
        rename_type = step.get("rename_type") or {}
        if isinstance(rename_type, dict):
            new_type = rename_type.get(out["record_type"])
            if isinstance(new_type, str):
                out["record_type"] = new_type
        rename_fields = step.get("rename_field") or {}
        fields: JsonObject | None = None
        if isinstance(rename_fields, dict):
            raw_fields = rename_fields.get(out["record_type"])
            if isinstance(raw_fields, dict):
                fields = raw_fields
        if fields is None:
            fields = {}
        for old, new in fields.items():
            if not isinstance(new, str):
                continue
            if old in payload:
                payload[new] = payload.pop(old)
        map_enum = step.get("map_enum") or {}
        if not isinstance(map_enum, dict):
            continue
        for key, raw_mapping in map_enum.items():
            if not isinstance(raw_mapping, dict):
                continue
            record_type, field = key.rsplit(".", 1)
            if record_type == out["record_type"] and field in payload:
                payload[field] = _map_value(raw_mapping, payload[field])
    out["payload"] = payload
    return out


def _changed(before: Record, after: Record) -> bool:
    return before["record_type"] != after["record_type"] or before.get("payload") != after.get(
        "payload"
    )


def apply_steps(store: Backend, steps: list[JsonObject]) -> int:
    """Rewrite every record and history snapshot the steps touch. Returns the live record count."""
    for snapshot in list(store.read_history()):
        moved = transform(snapshot, steps)
        if not _changed(snapshot, moved):
            continue
        moved = with_revision(prepare_record(moved))
        store.archive_history(moved)
        store.delete_history_snapshot(snapshot["record_type"], snapshot["id"], snapshot["revision"])
    rewritten = 0
    for record in list(store.iter_records()):
        moved = transform(record, steps)
        if not _changed(record, moved):
            continue
        moved = with_revision(prepare_record(moved))
        store.write_record(moved, expected_revision=record["revision"])
        rewritten += 1
    return rewritten


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))
