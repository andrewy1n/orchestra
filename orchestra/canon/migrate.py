"""Declarative schema migrations over the records and history of a store."""

from __future__ import annotations

from typing import Any

from orchestra.canon.record import prepare_record
from orchestra.canon.revision import with_revision
from orchestra.canon.schema import SchemaError
from orchestra.canon.backend import Backend


def migration_path(module: dict[str, Any], old_major: int, new_major: int) -> list[dict[str, Any]]:
    steps = {int(step["from"]): step for step in module.get("migrations") or []}
    path: list[dict[str, Any]] = []
    current = old_major
    while current < new_major:
        step = steps.get(current)
        if step is None or int(step["to"]) > new_major:
            raise SchemaError(
                f"{module['namespace']}: no migration from major {current} toward {new_major}"
            )
        path.append(step)
        current = int(step["to"])
    return path


def _map_value(mapping: dict[str, str], value: Any) -> Any:
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [_map_value(mapping, item) for item in value]
    return value


def transform(record: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
    out = dict(record)
    payload = dict(out.get("payload") or {})
    for step in steps:
        out["record_type"] = (step.get("rename_type") or {}).get(
            out["record_type"], out["record_type"]
        )
        for old, new in ((step.get("rename_field") or {}).get(out["record_type"]) or {}).items():
            if old in payload:
                payload[new] = payload.pop(old)
        for key, mapping in (step.get("map_enum") or {}).items():
            record_type, field = key.rsplit(".", 1)
            if record_type == out["record_type"] and field in payload:
                payload[field] = _map_value(mapping, payload[field])
    out["payload"] = payload
    return out


def _changed(before: dict[str, Any], after: dict[str, Any]) -> bool:
    return before["record_type"] != after["record_type"] or before.get("payload") != after.get(
        "payload"
    )


def apply_steps(store: Backend, steps: list[dict[str, Any]]) -> int:
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
