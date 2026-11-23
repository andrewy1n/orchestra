from __future__ import annotations

import pytest

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import JsonObject, Record
from orchestra.score.planning.effort import (
    current_effort,
    current_efforts,
    read_effort,
    scan_effort_records,
)


def _effort_record(
    record_id: str,
    *,
    subject: str = "alpha",
    payload: JsonObject | None = None,
    lifecycle_state: str = "active",
    recorded_at: str = "2026-01-01T00:00:00Z",
    write_order: int = 0,
) -> Record:
    return {
        "id": record_id,
        "record_type": "score:effort",
        "subject": subject,
        "payload": {"goal": "Ship", "kind": "deliver"} if payload is None else payload,
        "lifecycle_state": lifecycle_state,
        "relationships": {},
        "revision": "rev-1",
        "recorded_at": recorded_at,
        "derived": {"write_order": write_order},
    }


def test_equal_time_efforts_pick_the_later_written() -> None:
    earlier = _effort_record("a-1", write_order=1)
    later = _effort_record("a-2", write_order=2)

    current = current_effort([later, earlier], "alpha")

    assert current is not None
    assert current.id == "a-2"


def test_superseded_effort_is_not_current() -> None:
    old = _effort_record("a-1", recorded_at="2026-01-02T00:00:00Z", lifecycle_state="superseded")
    live = _effort_record("a-2", recorded_at="2026-01-01T00:00:00Z")

    assert current_efforts([old, live])["alpha"].id == "a-2"


def test_effort_without_goal_is_rejected() -> None:
    record = _effort_record("a-1", payload={"kind": "deliver"})

    with pytest.raises(RecordShapeError) as error:
        read_effort(record)

    assert (error.value.record_id, error.value.field) == ("a-1", "goal")


def test_scan_reports_one_finding_per_malformed_live_effort() -> None:
    bad = _effort_record(
        "a-1", subject="beta", payload={"goal": "Ship", "kind": "deliver", "status": "paused"}
    )
    dead = _effort_record("a-2", payload={}, lifecycle_state="superseded")
    good = _effort_record("a-3")

    findings = scan_effort_records([bad, dead, good])

    assert [(f.record_id, f.field) for f in findings] == [("a-1", "status")]
