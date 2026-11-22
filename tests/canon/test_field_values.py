from __future__ import annotations

from orchestra.canon.field_values import field_value, integer_field, named_fields
from orchestra.canon.types import JsonObject, Record


def _record(
    record_type: str,
    payload: JsonObject,
    subject: str = "s",
    state: str = "active",
    stamp: str = "2026-11-01T00:00:00Z",
) -> Record:
    return {
        "id": f"<{record_type}:{subject}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": "r1",
        "recorded_at": stamp,
    }


def test_field_value_returns_payload_value_or_default() -> None:
    record = _record("score:phase", {"title": "t"})
    assert field_value(record, "title") == "t"
    assert field_value(record, "missing") is None
    assert field_value(record, "missing", "fallback") == "fallback"


def test_integer_field_accepts_integers_only() -> None:
    assert integer_field(_record("score:phase", {"ordinal": 4}), "ordinal") == 4
    assert integer_field(_record("score:phase", {"ordinal": True}), "ordinal") is None
    assert integer_field(_record("score:phase", {"ordinal": "4"}), "ordinal") is None
    assert integer_field(_record("score:phase", {}), "ordinal") is None


def test_named_fields_keep_order_and_mark_missing_as_none() -> None:
    record = _record("score:phase", {"b": 1, "a": "x"})
    assert named_fields(record, ["a", "c", "b"]) == [("a", "x"), ("c", None), ("b", 1)]
