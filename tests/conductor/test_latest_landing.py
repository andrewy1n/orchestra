from __future__ import annotations

from orchestra.canon.types import Record
from orchestra.conductor.landing import latest_landing


def _landing(phase: str, result: str, recorded_at: str, write_order: int = 0) -> Record:
    return {
        "id": f"rec-{phase}-{result}",
        "record_type": "conductor:landing",
        "subject": phase,
        "payload": {
            "phase": phase,
            "number": 7,
            "url": "https://github.com/o/r/pull/7",
            "head_sha": "a" * 40,
            "result": result,
        },
        "lifecycle_state": "recorded",
        "relationships": {},
        "revision": "sha256:x",
        "recorded_at": recorded_at,
        "body": "",
        "derived": {"write_order": write_order},
    }


def test_latest_landing_is_none_without_a_record() -> None:
    assert latest_landing([], "p1") is None


def test_latest_landing_picks_the_newest_record_of_the_phase() -> None:
    older = _landing("p1", "fail", "2026-11-08T10:00:00+00:00")
    newer = _landing("p1", "success", "2026-11-08T10:30:00+00:00")
    other = _landing("p2", "fail", "2026-11-08T11:00:00+00:00")

    found = latest_landing([newer, other, older], "p1")
    assert found is not None
    assert found.record == newer


def test_latest_landing_breaks_a_timestamp_tie_by_write_order() -> None:
    success = _landing("p1", "success", "2026-11-08T10:00:00+00:00", write_order=1)
    fail = _landing("p1", "fail", "2026-11-08T10:00:00+00:00", write_order=2)
    assert fail["id"] < success["id"]

    for records in ([success, fail], [fail, success]):
        found = latest_landing(records, "p1")
        assert found is not None
        assert found.record == fail
