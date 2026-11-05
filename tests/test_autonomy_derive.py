from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone

from orchestra.canon.types import JsonObject, Record
from orchestra.derive import effort_autonomy, effort_dormant

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
_IDS = itertools.count()


def _record(
    record_type: str,
    subject: str,
    payload: JsonObject,
    age_days: float,
    state: str = "current",
) -> Record:
    n = next(_IDS)
    stamp = (NOW - timedelta(days=age_days)).isoformat()
    return {
        "id": f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": stamp,
    }


def _goal(age_days: float, **extra: str) -> Record:
    return _record("score:effort", "e", {"goal": "g", "kind": "deliver", **extra}, age_days)


def _phase(age_days: float, state: str) -> Record:
    payload: JsonObject = {"title": "p", "ordinal": 1, "effort": "e"}
    return _record("score:phase", "p1", payload, age_days, state)


def test_autonomy_level_defaults_to_gated() -> None:
    assert effort_autonomy([_goal(1)], "e") == "gated"
    assert effort_autonomy([_goal(1, autonomy="auto-plan")], "e") == "auto-plan"
    assert effort_autonomy([_goal(1, autonomy="auto-phases")], "e") == "auto-phases"


def test_r09_an_open_effort_with_no_live_phase_and_a_quiet_week_is_dormant() -> None:
    records = [_goal(8), _phase(8, "done")]
    assert effort_dormant(records, "e", NOW)


def test_r09_a_change_within_seven_days_keeps_the_effort_active() -> None:
    position = _record(
        "score:position", "e", {"position": "x", "scope": "effort", "effort": "e"}, 6.5
    )
    assert not effort_dormant([_goal(30), position], "e", NOW)


def test_r09_a_planned_or_in_progress_phase_keeps_the_effort_active() -> None:
    for state in ("planned", "in_progress"):
        assert not effort_dormant([_goal(30), _phase(30, state)], "e", NOW)


def test_r09_a_closed_effort_is_not_dormant() -> None:
    assert not effort_dormant([_goal(30, status="closed")], "e", NOW)


def test_r09_dormancy_does_not_change_the_effort_status() -> None:
    goal = _goal(30)
    assert effort_dormant([goal], "e", NOW)
    assert "status" not in goal["payload"]


def test_r13_a_new_phase_makes_a_dormant_effort_active_again() -> None:
    records = [_goal(30)]
    assert effort_dormant(records, "e", NOW)
    records.append(_phase(0, "planned"))
    assert not effort_dormant(records, "e", NOW)
