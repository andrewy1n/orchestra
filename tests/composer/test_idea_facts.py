from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.composer.idea_facts import (
    IDEA_TYPE,
    idea_status,
    is_open_backlog_idea,
    is_roadmap_idea,
)


def _record(
    record_type: str,
    payload: JsonObject,
    subject: str = "s",
    state: str = "active",
    stamp: str = "2026-11-01T00:00:00Z",
) -> Record:
    return {
        "id": f"<{record_type}:{subject}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": "r1",
        "recorded_at": stamp,
    }


def test_idea_status_reads_text_status_only() -> None:
    assert idea_status(_record(IDEA_TYPE, {"status": "open"})) == "open"
    assert idea_status(_record(IDEA_TYPE, {"status": 1})) is None
    assert idea_status(_record(IDEA_TYPE, {})) is None


def test_open_backlog_idea_needs_open_status_and_effort() -> None:
    assert is_open_backlog_idea(_record(IDEA_TYPE, {"status": "open", "effort": "alpha"}))
    assert not is_open_backlog_idea(_record(IDEA_TYPE, {"status": "open", "effort": ""}))
    assert not is_open_backlog_idea(_record(IDEA_TYPE, {"status": "promoted", "effort": "alpha"}))


def test_roadmap_idea_is_open_or_promoted() -> None:
    assert is_roadmap_idea(_record(IDEA_TYPE, {"status": "open"}))
    assert is_roadmap_idea(_record(IDEA_TYPE, {"status": "promoted"}))
    assert not is_roadmap_idea(_record(IDEA_TYPE, {"status": "dismissed"}))
