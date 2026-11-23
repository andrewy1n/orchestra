from __future__ import annotations

import pytest

from orchestra.canon.types import JsonObject, Record
from orchestra.score.planning.milestone import MilestoneFacts, milestone_facts, milestone_state


def _milestone(subject: str, payload: JsonObject) -> Record:
    return {
        "id": f"<score:milestone:{subject}>",
        "record_type": "score:milestone",
        "subject": subject,
        "payload": payload,
        "lifecycle_state": "planned",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00Z",
    }


def test_milestone_facts_read_title_and_ordinal() -> None:
    record = _milestone("m-one", {"title": "First", "ordinal": 3})
    assert milestone_facts(record) == MilestoneFacts(
        id="<score:milestone:m-one>", subject="m-one", title="First", ordinal=3
    )


@pytest.mark.parametrize("payload", [{}, {"title": ""}, {"title": 7}])
def test_milestone_facts_title_falls_back_to_subject(payload: JsonObject) -> None:
    assert milestone_facts(_milestone("m-one", payload)).title == "m-one"


@pytest.mark.parametrize("payload", [{}, {"ordinal": "2"}, {"ordinal": True}])
def test_milestone_facts_ordinal_defaults_to_zero(payload: JsonObject) -> None:
    assert milestone_facts(_milestone("m-one", payload)).ordinal == 0


@pytest.mark.parametrize(
    ("states", "expected"),
    [
        ([], "planned"),
        (["planned", "planned"], "planned"),
        (["planned", "in_progress", "done"], "in_progress"),
        (["done", "done"], "done"),
        (["done", "planned"], "planned"),
        (["done"], "done"),
    ],
)
def test_milestone_state_follows_member_phase_states(states: list[str], expected: str) -> None:
    assert milestone_state(states) == expected
