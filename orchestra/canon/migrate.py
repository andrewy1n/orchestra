"""Declarative schema migrations over the records and history of a store."""

from __future__ import annotations

from typing import TypedDict

from orchestra.canon.backend import Backend
from orchestra.canon.record import prepare_record
from orchestra.canon.revision import with_revision
from orchestra.canon.schema import SchemaError
from orchestra.canon.types import JsonObject, JsonValue, Record

_Migration = TypedDict(
    "_Migration",
    {
        "from": str | int | float | bool,
        "to": str | int | float | bool,
        "rename_type": dict[object, JsonValue],
        "rename_field": dict[object, dict[str, JsonValue]],
        "map_enum": dict[str, dict[str, JsonValue]],
    },
)


def migration_path(module: JsonObject, old_major: int, new_major: int) -> list[JsonObject]:
    migrations: list[_Migration] = module.get("migrations") or []  # pyright: ignore[reportAssignmentType]  # Schema validation supplies migration objects; runtime values remain unaltered.
    steps: dict[int, JsonObject] = {int(step["from"]): step for step in migrations}  # pyright: ignore[reportAssignmentType]  # Steps retain the raw validated JSON objects.
    path: list[JsonObject] = []
    current = old_major
    while current < new_major:
        step = steps.get(current)
        if step is None:
            raise SchemaError(
                f"{module['namespace']}: no migration from major {current} toward {new_major}"
            )
        target = int(step["to"])  # pyright: ignore[reportArgumentType]  # Migration versions retain legacy int coercion.
        if target > new_major:
            raise SchemaError(
                f"{module['namespace']}: no migration from major {current} toward {new_major}"
            )
        path.append(step)
        current = target
    return path


def _map_value(mapping: dict[str, JsonValue], value: JsonValue) -> JsonValue:
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [_map_value(mapping, item) for item in value]
    return value


def transform(record: Record, steps: list[JsonObject]) -> Record:
    out: Record = record.copy()
    payload = dict(out.get("payload") or {})
    typed_steps: list[_Migration] = steps  # pyright: ignore[reportAssignmentType]  # Schema validation supplies migration objects; runtime values remain unaltered.
    previous_type: JsonValue = out["record_type"]
    for step in typed_steps:
        new_type = (step.get("rename_type") or {}).get(previous_type, previous_type)
        out["record_type"] = new_type  # pyright: ignore[reportGeneralTypeIssues]  # Migration targets retain legacy JSON values.
        previous_type = new_type
        fields = (step.get("rename_field") or {}).get(previous_type) or {}
        for old, new in fields.items():
            if old in payload:
                payload[new] = payload.pop(old)  # pyright: ignore[reportArgumentType]  # Rename targets retain legacy JSON key behavior.
        map_enum = step.get("map_enum") or {}
        for key, mapping in map_enum.items():
            record_type, field = key.rsplit(".", 1)
            if record_type == out["record_type"] and field in payload:
                payload[field] = _map_value(mapping, payload[field])
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
