from __future__ import annotations

import pytest

from orchestra.canon.types import JsonObject, Record
from orchestra.score.facts.work_item_facts import tasks_by_requirement
from orchestra.score.planning.scope import (
    design_decisions,
    records_for_phase,
    spec_requirements,
    spec_weight,
)


def _record(subject: str, payload: JsonObject, state: str = "active", n: int = 0) -> Record:
    return {
        "id": f"<{subject}>",
        "record_type": "score:work-item",
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:00:{n:02d}Z",
    }


def test_records_for_phase_keeps_matching_phase_and_effort() -> None:
    records = [
        _record("a", {"phase": "p", "effort": "e"}),
        _record("b", {"phase": "p", "effort": "other"}),
        _record("c", {"phase": "q", "effort": "e"}),
    ]
    assert [r["subject"] for r in records_for_phase(records, "p", "e")] == ["a"]


def test_records_for_phase_accepts_a_record_without_effort() -> None:
    records = [_record("a", {"phase": "p"}), _record("b", {"phase": "p", "effort": ""})]
    assert [r["subject"] for r in records_for_phase(records, "p", "e")] == ["a", "b"]


@pytest.mark.parametrize("state", ["superseded", "retracted"])
def test_records_for_phase_drops_inactive_records(state: str) -> None:
    records = [_record("a", {"phase": "p"}, state), _record("b", {"phase": "p"}, "done")]
    assert [r["subject"] for r in records_for_phase(records, "p", "e")] == ["b"]


@pytest.mark.parametrize(
    ("payload", "expected"),
    [({"weight": "light"}, "light"), ({"weight": "full"}, "full"), ({}, ""), ({"weight": 3}, "")],
)
def test_spec_weight_reads_the_weight_text(payload: JsonObject, expected: str) -> None:
    assert spec_weight(_record("s", payload)) == expected


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"decisions": ["d-one", "d-two"]}, ("d-one", "d-two")),
        ({"decisions": ["d-one", 4, "d-two"]}, ("d-one", "d-two")),
        ({"decisions": "d-one"}, ()),
        ({}, ()),
    ],
)
def test_design_decisions_lists_decision_subjects(
    payload: JsonObject, expected: tuple[str, ...]
) -> None:
    assert design_decisions(_record("d", payload)) == expected


def test_tasks_by_requirement_groups_phase_tasks_once_per_requirement() -> None:
    first = _record("a", {"phase": "p", "requirements": ["R1", "R1", "R2"]}, "planned")
    second = _record("b", {"phase": "p", "requirements": ["R1"]}, "done")
    grouped = tasks_by_requirement([first, second], "p")
    assert {key: [r["subject"] for r in value] for key, value in grouped.items()} == {
        "R1": ["a", "b"],
        "R2": ["a"],
    }


def test_tasks_by_requirement_skips_superseded_other_phase_and_unlisted_tasks() -> None:
    tasks = [
        _record("old", {"phase": "p", "requirements": ["R1"]}, "superseded"),
        _record("elsewhere", {"phase": "q", "requirements": ["R1"]}, "planned"),
        _record("bare", {"phase": "p"}, "planned"),
        _record("bad", {"phase": "p", "requirements": "R1"}, "planned"),
        _record("kept", {"phase": "p", "requirements": ["R3"]}, "withdrawn"),
    ]
    grouped = tasks_by_requirement(tasks, "p")
    assert {key: [r["subject"] for r in value] for key, value in grouped.items()} == {
        "R3": ["kept"]
    }


@pytest.mark.parametrize(
    ("payload", "expected"),
    [({"requirements": ["R1", 2, "R2"]}, ("R1", "R2")), ({"requirements": "R1"}, ()), ({}, ())],
)
def test_spec_requirements_lists_requirement_ids(
    payload: JsonObject, expected: tuple[str, ...]
) -> None:
    assert spec_requirements(_record("s", payload)) == expected
