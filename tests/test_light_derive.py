from __future__ import annotations

import itertools

from orchestra.canon.types import JsonObject, Record
from orchestra.derive import release_ready, requirement_status

_CLOCK = itertools.count()


def _record(
    record_type: str, subject: str, payload: JsonObject, body: str = "", state: str = "active"
) -> Record:
    n = next(_CLOCK)
    return {
        "id": f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:00:{n:02d}Z",
        "body": body,
    }


def _light_records(result: str) -> list[Record]:
    phase = _record(
        "score:phase",
        "p",
        {"weight": "light"},
        "## Requirements\n\nR1: One.\nR2: Two.\n",
        "in_progress",
    )
    acceptance = _record("score:acceptance", "a", {"phase": "p", "requirements": ["R1", "R2"]})
    run = _record(
        "tuner:check-run",
        "a",
        {"criterion_id": acceptance["id"], "result": result, "revision": "abc"},
        state="recorded",
    )
    return [phase, acceptance, run]


def test_multi_requirement_check_run_verifies_each_listed_requirement() -> None:
    statuses = requirement_status(_light_records("pass"), "p")
    assert {rid: s.status for rid, s in statuses.items()} == {"R1": "verified", "R2": "verified"}
    assert release_ready(_light_records("pass"), "p")


def test_multi_requirement_failing_check_run_fails_each_listed_requirement() -> None:
    statuses = requirement_status(_light_records("fail"), "p")
    assert {rid: s.status for rid, s in statuses.items()} == {"R1": "failed", "R2": "failed"}
