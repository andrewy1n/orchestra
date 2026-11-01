"""Git-backed typed record store."""

from __future__ import annotations

from orchestra.canon.types import JsonObject, JsonValue, Record, get_string

__all__ = ["JsonObject", "JsonValue", "Record", "get_string", "record_payload"]

__version__ = "0.1.0"


def record_payload(record: Record | JsonObject) -> JsonObject:
    payload = record.get("payload")
    return payload if isinstance(payload, dict) else {}
