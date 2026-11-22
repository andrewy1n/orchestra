from __future__ import annotations

import pytest

from orchestra.canon.types import JsonObject, Record
from orchestra.tuner.record_facts import check_run_facts


def _run(extra: JsonObject) -> Record:
    payload: JsonObject = {
        "criterion_id": "<acc>",
        "revision": "abc",
        "result": "pass",
        "method": "check",
        "signed_by": "",
        **extra,
    }
    return {
        "id": "<run>",
        "record_type": "tuner:check-run",
        "subject": "run",
        "payload": payload,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00Z",
    }


@pytest.mark.parametrize(
    ("payload", "expected"),
    [({"requirement": "R2"}, "R2"), ({}, ""), ({"requirement": 2}, "")],
)
def test_check_run_facts_carry_the_requirement_name(payload: JsonObject, expected: str) -> None:
    assert check_run_facts(_run(payload)).requirement == expected
