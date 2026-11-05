"""Declarative schema migrations over the records and history of a store."""

from __future__ import annotations

from typing import TypedDict

from orchestra.canon.backend import Backend
from orchestra.canon.record import prepare_record
from orchestra.canon.revision import with_revision
from orchestra.canon.schema import SchemaError
from orchestra.canon.types import JsonObject, JsonValue, Record, get_list, get_object, get_string

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


def _map_value(
    mapping: dict[str, JsonValue], value: JsonValue, allowed: list[str] | None
) -> JsonValue:
    if isinstance(value, str):
        if value in mapping:
            return mapping[value]
        if allowed is None or value in allowed:
            return value
        raise SchemaError(f"enum value {value!r} has no migration mapping")
    if isinstance(value, list):
        return [_map_value(mapping, item, allowed) for item in value]
    return value


def transform(
    record: Record, steps: list[JsonObject], target_module: JsonObject | None = None
) -> Record:
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
                allowed: list[str] | None = None
                if target_module is not None:
                    types = get_object(target_module, "types") or {}
                    type_def = get_object(types, record_type.split(":", 1)[1])
                    fields = get_object(type_def, "fields") if type_def is not None else None
                    enum_form = get_object(fields, field) if fields is not None else None
                    values = get_list(enum_form, "enum") if enum_form is not None else None
                    if values is not None:
                        allowed = [value for value in values if isinstance(value, str)]
                payload[field] = _map_value(mapping, payload[field], allowed)
    out["payload"] = payload
    return out


def _changed(before: Record, after: Record) -> bool:
    return before["record_type"] != after["record_type"] or before.get("payload") != after.get(
        "payload"
    )


def apply_steps(
    store: Backend, steps: list[JsonObject], target_module: JsonObject | None = None
) -> int:
    """Rewrite every record and history snapshot the steps touch. Returns the live record count."""
    snapshots = list(store.read_history())
    records = list(store.iter_records())
    if target_module is not None:
        namespace = get_string(target_module, "namespace")
        target_types = get_object(target_module, "types") or {}
        if namespace is None:
            raise SchemaError("migration target namespace is missing")
        valid_types = [f"{namespace}:{name}" for name in target_types]
        for record in [*snapshots, *records]:
            moved = transform(record, steps, target_module)
            record_type = record["record_type"]
            moved_type = moved["record_type"]
            if record_type.startswith(f"{namespace}:") and moved_type not in valid_types:
                raise SchemaError(f"{record_type}: migration has no valid target type mapping")
    for snapshot in snapshots:
        moved = transform(snapshot, steps, target_module)
        if not _changed(snapshot, moved):
            continue
        moved = with_revision(prepare_record(moved))
        store.archive_history(moved)
        store.delete_history_snapshot(snapshot["record_type"], snapshot["id"], snapshot["revision"])
    rewritten = 0
    for record in records:
        moved = transform(record, steps, target_module)
        if not _changed(record, moved):
            continue
        moved = with_revision(prepare_record(moved))
        store.write_record(moved, expected_revision=record["revision"])
        rewritten += 1
    return rewritten


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))
