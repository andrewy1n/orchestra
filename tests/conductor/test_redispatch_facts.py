from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.redispatch_facts import redispatch_facts


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


def test_redispatch_facts_carry_dispatch_payload_fields() -> None:
    record = _record(
        "score:work-item",
        {
            "attempts": 2,
            "dispatch_id": "d1",
            "dispatch_started_at": "2026-11-01T00:00:00Z",
            "assignee": "subagent",
            "write_root": "w",
        },
        subject="task-a",
    )
    facts = redispatch_facts(record)
    assert (facts.task, facts.revision, facts.attempts) == ("task-a", "r1", 2)
    assert (facts.dispatch_id, facts.dispatch_started_at) == ("d1", "2026-11-01T00:00:00Z")
    assert (facts.assignee, facts.write_root) == ("subagent", "w")


def test_redispatch_facts_leave_missing_fields_none() -> None:
    facts = redispatch_facts(_record("score:work-item", {}))
    assert facts.attempts is None
    assert facts.assignee is None
