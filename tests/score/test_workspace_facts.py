from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.score.facts.workspace_facts import (
    ConstraintFacts,
    DecisionFacts,
    EffortSummary,
    constraint_facts,
    decision_facts,
    effort_positions,
    effort_summary,
    work_item_efforts,
)


def _record(record_type: str, subject: str, payload: JsonObject, state: str = "active") -> Record:
    return {
        "id": f"<{record_type}:{subject}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00Z",
    }


def test_decision_facts_read_text_fields() -> None:
    record = _record("score:decision", "d", {"phase": "p", "choice": "a", "alternatives": "b"})
    assert decision_facts(record) == DecisionFacts("p", "a", "b")


def test_decision_facts_default_missing_and_non_text_to_empty() -> None:
    record = _record("score:decision", "d", {"choice": 3})
    assert decision_facts(record) == DecisionFacts("", "", "")


def test_constraint_facts_read_applies_to_and_statement() -> None:
    record = _record("score:constraint", "c", {"applies_to": "p", "statement": "s"})
    assert constraint_facts(record) == ConstraintFacts("p", "s")
    assert constraint_facts(_record("score:constraint", "c", {})) == ConstraintFacts("", "")


def test_effort_summary_reads_goal_and_kind() -> None:
    record = _record("score:effort", "e", {"goal": "g", "kind": "repair"})
    assert effort_summary(record) == EffortSummary("g", "repair")
    assert effort_summary(_record("score:effort", "e", {})) == EffortSummary("", "")


def test_work_item_efforts_map_id_and_first_subject() -> None:
    first = _record("score:work-item", "t", {"effort": "e1"}, "planned")
    second = _record("score:work-item", "t", {"effort": "e2"}, "planned")
    second["id"] = "<score:work-item:t-2>"
    bare = _record("score:work-item", "u", {}, "planned")
    assert work_item_efforts([first, second, bare]) == {
        first["id"]: ("e1", "t"),
        second["id"]: ("e2", "t"),
        "t": ("e1", "t"),
        bare["id"]: ("", "u"),
        "u": ("", "u"),
    }


def test_effort_positions_keep_only_active_open_effort_scope() -> None:
    kept = _record("score:position", "e1", {"scope": "effort", "position": "here"})
    closed = _record(
        "score:position", "e2", {"scope": "effort", "status": "closed", "position": "x"}
    )
    other_scope = _record("score:position", "e3", {"scope": "phase", "position": "x"})
    retired = _record("score:position", "e4", {"scope": "effort", "position": "x"}, "superseded")
    blank = _record("score:position", "e5", {"scope": "effort"})
    assert effort_positions([kept, closed, other_scope, retired, blank]) == {
        "e1": "here",
        "e5": "",
    }
