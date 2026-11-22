from __future__ import annotations

from orchestra.canon import record_payload
from orchestra.canon.types import JsonValue, Record


def payload_field_equals(record: Record, field: str, expected: str) -> bool:
    return record_payload(record).get(field) == expected


def payload_items(record: Record) -> list[tuple[str, JsonValue]]:
    return list(record_payload(record).items())
