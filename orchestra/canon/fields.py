from __future__ import annotations

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import JsonObject, Record


def required_text(record: Record, payload: JsonObject, field: str) -> str:
    if field not in payload:
        raise RecordShapeError(record["id"], field, "is required")
    value = payload[field]
    if not isinstance(value, str):
        raise RecordShapeError(record["id"], field, "must be a string")
    return value


def optional_text(record: Record, payload: JsonObject, field: str) -> str | None:
    if field not in payload:
        return None
    value = payload[field]
    if not isinstance(value, str):
        raise RecordShapeError(record["id"], field, "must be a string")
    if not value:
        raise RecordShapeError(record["id"], field, "must not be empty")
    return value


def required_int(record: Record, payload: JsonObject, field: str) -> int:
    if field not in payload:
        raise RecordShapeError(record["id"], field, "is required")
    value = payload[field]
    if isinstance(value, bool) or not isinstance(value, int):
        raise RecordShapeError(record["id"], field, "must be an integer")
    return value
