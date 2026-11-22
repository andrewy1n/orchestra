from __future__ import annotations

import pytest
from orchestra.conductor.release_facts import integration_result, is_release_ready, release_state

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.requirements import RequirementState, RequirementStatus


def _record(record_type: str, payload: JsonObject) -> Record:
    return {
        "id": f"<{record_type}>",
        "record_type": record_type,
        "subject": "s",
        "payload": payload,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00Z",
    }


def _statuses(*states: RequirementState) -> dict[str, RequirementStatus]:
    return {
        f"R{index}": RequirementStatus(requirement=f"R{index}", status=state)
        for index, state in enumerate(states, 1)
    }


@pytest.mark.parametrize(
    ("payload", "expected"),
    [({"state": "merged"}, "merged"), ({}, ""), ({"state": 3}, "")],
)
def test_release_state_reads_the_state_text(payload: JsonObject, expected: str) -> None:
    assert release_state(_record("conductor:release", payload)) == expected


@pytest.mark.parametrize(
    ("payload", "expected"),
    [({"result": "fail"}, "fail"), ({}, ""), ({"result": None}, "")],
)
def test_integration_result_reads_the_result_text(payload: JsonObject, expected: str) -> None:
    assert integration_result(_record("conductor:integration-report", payload)) == expected


def test_a_ready_release_makes_the_phase_release_ready_without_verified_requirements() -> None:
    release = _record("conductor:release", {"state": "ready"})
    assert is_release_ready(release, _statuses("failed", "unverified")) is True


def test_a_later_release_state_leaves_readiness_to_the_requirements() -> None:
    release = _record("conductor:release", {"state": "merged"})
    assert is_release_ready(release, _statuses("verified")) is True
    assert is_release_ready(release, _statuses("verified", "failed")) is False


def test_without_a_release_readiness_needs_every_requirement_verified() -> None:
    assert is_release_ready(None, _statuses("verified", "verified")) is True
    assert is_release_ready(None, _statuses("verified", "unverified")) is False
    assert is_release_ready(None, {}) is False
