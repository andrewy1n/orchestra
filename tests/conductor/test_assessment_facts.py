from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.phases.progress.assessment_facts import (
    AssessmentFacts,
    AssessmentSummary,
    assessment_facts,
    assessment_summary,
    latest_assessments,
)


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


def _summary_record(
    subject: str, payload: JsonObject, n: int, supersedes: list[str] | None = None
) -> Record:
    record = _assessment(subject, payload, n=n)
    if supersedes:
        record["relationships"] = {"supersedes": supersedes}
    return record


def test_assessment_summary_joins_requirement_status_and_next() -> None:
    record = _summary_record("a", {"requirement": "R1", "status": "verified", "next": "release"}, 1)
    assert assessment_summary(record, {}) == AssessmentSummary("R1 verified release", False)


def test_assessment_summary_marks_failed_and_blocked_as_failed() -> None:
    for status in ("failed", "blocked"):
        record = _summary_record("a", {"requirement": "R1", "status": status, "next": "x"}, 1)
        assert assessment_summary(record, {}).failed is True
    record = _summary_record("a", {"requirement": "R1", "status": "insufficient"}, 1)
    assert assessment_summary(record, {}).failed is False


def test_assessment_summary_marks_upstream_next_steps() -> None:
    for step in ("specify", "design", "plan"):
        record = _summary_record("a", {"requirement": "R1", "status": "x", "next": step}, 1)
        assert assessment_summary(record, {}).text == f"R1 x {step} upstream"
    record = _summary_record("a", {"requirement": "R1", "status": "x", "next": "execute"}, 1)
    assert assessment_summary(record, {}).text == "R1 x execute"


def test_assessment_summary_reports_a_level_change_from_the_superseded_record() -> None:
    old = _summary_record("old", {"requirement": "R1", "level": "design"}, 1)
    new = _summary_record(
        "new",
        {"requirement": "R1", "status": "x", "next": "plan", "level": "code"},
        2,
        supersedes=[old["id"]],
    )
    summary = assessment_summary(new, {old["id"]: old, new["id"]: new})
    assert summary.text == "R1 x plan upstream level design to code"


def test_assessment_summary_omits_the_level_when_it_is_unchanged_or_unlinked() -> None:
    old = _summary_record("old", {"requirement": "R1", "level": "design"}, 1)
    same = _summary_record(
        "new", {"requirement": "R1", "level": "design"}, 2, supersedes=[old["id"]]
    )
    assert assessment_summary(same, {old["id"]: old}).text == "R1  "
    assert assessment_summary(same, {}).text == "R1  "
