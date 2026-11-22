from __future__ import annotations

from orchestra.canon.payload_view import payload_field_equals, payload_items
from orchestra.canon.types import JsonObject, Record


def _record(payload: JsonObject) -> Record:
    return {
        "id": "<score:work-item:s>",
        "record_type": "score:work-item",
        "subject": "s",
        "payload": payload,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00Z",
    }


def test_payload_field_equals_matches_only_the_named_value() -> None:
    record = _record({"effort": "e1"})
    assert payload_field_equals(record, "effort", "e1")
    assert not payload_field_equals(record, "effort", "e2")
    assert not payload_field_equals(record, "phase", "e1")


def test_payload_field_equals_is_false_on_an_empty_payload() -> None:
    assert not payload_field_equals(_record({}), "effort", "e1")


def test_payload_items_keep_payload_order_and_values() -> None:
    assert payload_items(_record({"b": 1, "a": "x"})) == [("b", 1), ("a", "x")]
