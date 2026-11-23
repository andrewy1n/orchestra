from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.score.facts.detail_facts import ACCEPTANCE_TYPE, acceptance_facts
from orchestra.score.workflow.continuity import question_answer_operation


def _record(record_type: str, payload: JsonObject, subject: str = "s") -> Record:
    return {
        "id": f"<{record_type}:{subject}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00Z",
    }


def test_acceptance_facts_read_criterion_method_and_command() -> None:
    record = _record(
        ACCEPTANCE_TYPE, {"criterion": "works", "method": "check", "verify_command": "pytest"}
    )
    facts = acceptance_facts(record)
    assert (facts.criterion, facts.method, facts.verify_command) == ("works", "check", "pytest")


def test_acceptance_facts_default_missing_and_non_text_fields_to_empty() -> None:
    facts = acceptance_facts(_record(ACCEPTANCE_TYPE, {"method": 3}))
    assert (facts.criterion, facts.method, facts.verify_command) == ("", "", "")


def test_question_answer_operation_carries_note_as_answer() -> None:
    assert question_answer_operation("score:continuity-question", "q1", "r9", "yes") == {
        "op": "update",
        "type": "score:continuity-question",
        "id": "q1",
        "transition": "answered",
        "expected_revision": "r9",
        "payload": {"answer": "yes"},
    }


def test_question_answer_operation_omits_payload_without_note() -> None:
    operation = question_answer_operation("score:continuity-question", "q1", "r9", None)
    assert "payload" not in operation
