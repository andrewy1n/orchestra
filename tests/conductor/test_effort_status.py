from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.phases.progress.effort_status import effort_statuses

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
    return {
        "id": f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": (NOW - timedelta(days=age_days)).isoformat(),
    }


def _effort(age_days: float, status: str | None = None, subject: str = "e") -> Record:
    payload: JsonObject = {"goal": "g", "kind": "deliver"}
    if status is not None:
        payload["status"] = status
    return _record("score:effort", subject, payload, age_days)


def _phase(age_days: float, state: str, slug: str = "p1", effort: str = "e") -> Record:
    payload: JsonObject = {"title": "p", "ordinal": 1, "effort": effort}
    return _record("score:phase", slug, payload, age_days, state)


def _item(age_days: float, state: str, phase: str = "p1", subject: str = "w1") -> Record:
    return _record("score:work-item", subject, {"title": "w", "phase": phase}, age_days, state)


def _blocking_question(age_days: float) -> Record:
    return _record("score:continuity-question", "e", {"blocking": True}, age_days, "open")


def test_effort_with_closed_status_is_closed() -> None:
    records = [_effort(1, "closed"), _phase(1, "in_progress")]
    assert effort_statuses(records, NOW) == {"e": "closed"}


def test_effort_with_every_item_done_is_finished() -> None:
    records = [_effort(1), _phase(1, "done"), _item(1, "done")]
    assert effort_statuses(records, NOW) == {"e": "finished"}


def test_effort_without_phases_or_items_is_not_finished() -> None:
    assert effort_statuses([_effort(1)], NOW) == {"e": "live"}


def test_effort_with_an_unfinished_phase_is_not_finished() -> None:
    records = [_effort(1), _phase(1, "done"), _phase(1, "planned", slug="p2")]
    assert effort_statuses(records, NOW) == {"e": "live"}


def test_effort_quiet_for_seven_days_is_dormant() -> None:
    records = [_effort(7), _phase(7, "blocked")]
    assert effort_statuses(records, NOW) == {"e": "dormant"}


def test_effort_quiet_for_under_seven_days_is_live() -> None:
    records = [_effort(6.9)]
    assert effort_statuses(records, NOW) == {"e": "live"}


def test_effort_with_live_phase_is_not_dormant() -> None:
    assert effort_statuses([_effort(30), _phase(30, "in_progress")], NOW) == {"e": "live"}


def test_effort_with_blocking_question_is_not_dormant() -> None:
    assert effort_statuses([_effort(30), _blocking_question(30)], NOW) == {"e": "live"}


def test_effort_with_recent_activity_is_live() -> None:
    records = [_effort(30), _phase(1, "in_progress")]
    assert effort_statuses(records, NOW) == {"e": "live"}


def test_first_matching_status_wins() -> None:
    records = [
        _effort(30, "closed", subject="shut"),
        _phase(30, "done", slug="a", effort="shut"),
        _item(30, "done", phase="a", subject="wa"),
        _effort(30, subject="done"),
        _phase(30, "done", slug="b", effort="done"),
        _item(30, "done", phase="b", subject="wb"),
        _effort(30, subject="quiet"),
        _effort(1, subject="busy"),
    ]
    assert effort_statuses(records, NOW) == {
        "busy": "live",
        "done": "finished",
        "quiet": "dormant",
        "shut": "closed",
    }


def _phaseless_item(age_days: float, state: str, subject: str = "w2", effort: str = "e") -> Record:
    return _record("score:work-item", subject, {"title": "w", "effort": effort}, age_days, state)


def test_phaseless_open_item_keeps_done_phase_effort_live() -> None:
    records = [_effort(1), _phase(1, "done"), _phaseless_item(1, "planned")]
    assert effort_statuses(records, NOW) == {"e": "live"}


def test_phaseless_done_item_with_done_phase_is_finished() -> None:
    records = [_effort(1), _phase(1, "done"), _phaseless_item(1, "done")]
    assert effort_statuses(records, NOW) == {"e": "finished"}


def test_effort_with_only_phaseless_done_items_is_finished() -> None:
    records = [_effort(1), _phaseless_item(1, "done")]
    assert effort_statuses(records, NOW) == {"e": "finished"}
