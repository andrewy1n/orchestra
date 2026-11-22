from __future__ import annotations

from orchestra.conductor.assessment_facts import (
    AssessmentFacts,
    assessment_facts,
    latest_assessments,
)

from orchestra.canon.types import JsonObject, Record


def _assessment(subject: str, payload: JsonObject, state: str = "active", n: int = 0) -> Record:
    return {
        "id": f"<{subject}>",
        "record_type": "conductor:assessment",
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:00:{n:02d}Z",
    }


def test_assessment_facts_read_the_written_fields() -> None:
    record = _assessment(
        "a",
        {
            "phase": "p",
            "requirement": "R1",
            "status": "failed",
            "level": "design",
            "next": "execute",
            "confidence": "low",
        },
    )
    assert assessment_facts(record) == AssessmentFacts(
        phase="p",
        requirement="R1",
        status="failed",
        level="design",
        next="execute",
        confidence="low",
    )


def test_assessment_facts_default_missing_and_malformed_fields_to_empty_text() -> None:
    record = _assessment("a", {"phase": "p", "requirement": "R1", "level": 4, "next": None})
    assert assessment_facts(record) == AssessmentFacts(
        phase="p", requirement="R1", status="", level="", next="", confidence=""
    )


def test_latest_assessments_keeps_the_newest_per_requirement_of_the_phase() -> None:
    records = [
        _assessment("old", {"phase": "p", "requirement": "R1"}, n=1),
        _assessment("new", {"phase": "p", "requirement": "R1"}, n=2),
        _assessment("other", {"phase": "p", "requirement": "R2"}, n=0),
        _assessment("elsewhere", {"phase": "q", "requirement": "R1"}, n=9),
    ]
    latest = latest_assessments(records, "p")
    assert {key: record["subject"] for key, record in latest.items()} == {
        "R1": "new",
        "R2": "other",
    }


def test_latest_assessments_ignores_superseded_and_retracted_records() -> None:
    records = [
        _assessment("live", {"phase": "p", "requirement": "R1"}, n=1),
        _assessment("gone", {"phase": "p", "requirement": "R1"}, "superseded", n=2),
        _assessment("bad", {"phase": "p", "requirement": "R1"}, "retracted", n=3),
    ]
    assert latest_assessments(records, "p")["R1"]["subject"] == "live"


def test_latest_assessments_breaks_a_timestamp_tie_by_write_order() -> None:
    first = _assessment("first", {"phase": "p", "requirement": "R1"}, n=1)
    second = _assessment("second", {"phase": "p", "requirement": "R1"}, n=1)
    first["derived"] = {"write_order": 1}
    second["derived"] = {"write_order": 2}
    assert latest_assessments([second, first], "p")["R1"]["subject"] == "second"
