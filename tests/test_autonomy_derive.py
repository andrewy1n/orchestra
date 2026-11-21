from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.autonomy import effort_autonomy

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


def test_autonomy_level_defaults_to_gated() -> None:
    assert effort_autonomy([_goal(1)], "e") == "gated"
    assert effort_autonomy([_goal(1, autonomy="auto-plan")], "e") == "auto-plan"
    assert effort_autonomy([_goal(1, autonomy="auto-phases")], "e") == "auto-phases"
