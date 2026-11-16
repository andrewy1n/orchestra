from __future__ import annotations

from orchestra.canon.query import latest
from orchestra.canon.types import Record


def _record(record_id: str, recorded_at: str) -> Record:
    return {
        "id": record_id,
        "record_type": "score:phase",
        "subject": "slug",
        "payload": {},
        "lifecycle_state": "planned",
        "relationships": {},
        "revision": "revision",
        "recorded_at": recorded_at,
        "body": "",
    }


def test_r1_greatest_recorded_at_wins() -> None:
    older = _record("z", "2026-11-14T00:00:00Z")
    newer = _record("a", "2026-11-14T00:00:01Z")

    assert latest([newer, older]) == newer
    assert latest([older, newer]) == newer


def test_r1_equal_recorded_at_breaks_tie_by_greater_id() -> None:
    low = _record("a", "2026-11-14T00:00:00Z")
    high = _record("b", "2026-11-14T00:00:00Z")

    assert latest([low, high]) == high
    assert latest([high, low]) == high


def test_r1_empty_input_has_no_latest() -> None:
    assert latest([]) is None
