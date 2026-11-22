from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.score.view_facts import (
    CONSTRAINT_TYPE,
    EFFORT_TYPE,
    POSITION_TYPE,
    effort_constraint_lines,
    effort_of,
    effort_position_stamps,
    in_effort,
    is_closed,
)

WORK_ITEM = "score:work-item"


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


def test_effort_of_effort_record_is_its_subject() -> None:
    assert effort_of(_record(EFFORT_TYPE, {}, subject="alpha")) == "alpha"


def test_effort_of_reads_payload_effort_for_other_records() -> None:
    assert effort_of(_record(WORK_ITEM, {"effort": "alpha"})) == "alpha"


def test_effort_of_ignores_blank_and_non_text_effort() -> None:
    assert effort_of(_record(WORK_ITEM, {"effort": ""})) is None
    assert effort_of(_record(WORK_ITEM, {"effort": 3})) is None


def test_is_closed_only_for_closed_status() -> None:
    assert is_closed(_record(EFFORT_TYPE, {"status": "closed"}))
    assert not is_closed(_record(EFFORT_TYPE, {"status": "open"}))
    assert not is_closed(_record(EFFORT_TYPE, {}))


def test_in_effort_without_filter_accepts_every_record() -> None:
    assert in_effort(_record(WORK_ITEM, {}), None)


def test_in_effort_prefers_own_effort_over_scope() -> None:
    record = _record(WORK_ITEM, {"effort": "alpha", "scope": "beta"})
    assert in_effort(record, "alpha")
    assert not in_effort(record, "beta")


def test_in_effort_falls_back_to_scope_when_no_effort() -> None:
    record = _record("score:phase", {"scope": "beta"})
    assert in_effort(record, "beta")
    assert not in_effort(record, "alpha")


def test_effort_position_stamps_keep_newest_active_open_effort_scoped_stamp() -> None:
    records = [
        _record(
            POSITION_TYPE,
            {"effort": "alpha", "scope": "effort"},
            "p1",
            stamp="2026-11-01T00:00:01Z",
        ),
        _record(
            POSITION_TYPE,
            {"effort": "alpha", "scope": "effort"},
            "p2",
            stamp="2026-11-01T00:00:05Z",
        ),
        _record(
            POSITION_TYPE, {"effort": "alpha", "scope": "phase"}, "p3", stamp="2026-11-01T00:00:09Z"
        ),
        _record(
            POSITION_TYPE,
            {"effort": "alpha", "scope": "effort", "status": "closed"},
            "p4",
            stamp="2026-11-01T00:00:09Z",
        ),
        _record(
            POSITION_TYPE,
            {"effort": "alpha", "scope": "effort"},
            "p5",
            state="superseded",
            stamp="2026-11-01T00:00:09Z",
        ),
        _record(WORK_ITEM, {"effort": "beta", "scope": "effort"}, "w"),
    ]
    assert effort_position_stamps(records) == {"alpha": "2026-11-01T00:00:05Z"}


def test_effort_constraint_lines_select_active_constraints_of_listed_efforts_by_subject() -> None:
    records = [
        _record(CONSTRAINT_TYPE, {"effort": "alpha", "statement": "b rule"}, "b"),
        _record(CONSTRAINT_TYPE, {"effort": "alpha", "statement": "a rule"}, "a"),
        _record(CONSTRAINT_TYPE, {"effort": "beta", "statement": "other"}, "c"),
        _record(CONSTRAINT_TYPE, {"effort": "alpha", "statement": "old"}, "d", state="superseded"),
        _record(WORK_ITEM, {"effort": "alpha", "statement": "not a constraint"}, "e"),
    ]
    lines = effort_constraint_lines(records, {"alpha"})
    assert [(line.subject, line.statement) for line in lines] == [("a", "a rule"), ("b", "b rule")]


def test_effort_constraint_lines_default_missing_statement_to_empty() -> None:
    lines = effort_constraint_lines([_record(CONSTRAINT_TYPE, {"effort": "alpha"}, "a")], ["alpha"])
    assert [line.statement for line in lines] == [""]
