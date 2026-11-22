from __future__ import annotations

from collections.abc import Sequence

from orchestra.canon import record_payload
from orchestra.canon.types import JsonValue, Record


def field_value(record: Record, name: str, default: JsonValue = None) -> JsonValue:
    return record_payload(record).get(name, default)


def integer_field(record: Record, name: str) -> int | None:
    value = record_payload(record).get(name)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def named_fields(record: Record, names: Sequence[str]) -> list[tuple[str, JsonValue]]:
    payload = record_payload(record)
    return [(name, payload.get(name)) for name in names]
