from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.task_detail import (
    RELATED_KINDS,
    assignment_executor,
    related_text,
    report_facts,
    timeline_entries,
)


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


def test_assignment_executor_reads_text_or_empty() -> None:
    assert assignment_executor(_record("conductor:assignment", {"executor": "inline"})) == "inline"
    assert assignment_executor(_record("conductor:assignment", {})) == ""


def test_report_facts_read_result_verdict_and_revision() -> None:
    facts = report_facts(
        _record(
            "conductor:execution-report",
            {"result": "ok", "verdict": "pass", "revision": "abc"},
        )
    )
    assert (facts.result, facts.verdict, facts.revision) == ("ok", "pass", "abc")
    assert report_facts(_record("conductor:execution-report", {"verdict": 2})).verdict == ""


def test_related_text_reads_the_field_each_type_exposes() -> None:
    cases: dict[str, tuple[JsonObject, str]] = {
        "tuner:finding": ({"claim": "c"}, "c"),
        "score:decision": ({"choice": "x"}, "x"),
        "conductor:failed-attempt": ({"attempted_action": "a"}, "a"),
        "tuner:investigation-observation": ({"what_was_observed": "o"}, "o"),
    }
    assert set(cases) == set(RELATED_KINDS)
    for record_type, (payload, expected) in cases.items():
        assert related_text(_record(record_type, payload)) == expected


def test_related_text_is_empty_for_other_types_and_non_text_choice() -> None:
    assert related_text(_record("score:other", {"claim": "c"})) == ""
    assert related_text(_record("score:decision", {"choice": 3})) == ""


def test_timeline_entries_summarize_each_kind() -> None:
    entries = timeline_entries(
        [_record("conductor:assignment", {"executor": "inline"}, "a")],
        [_record("conductor:assignment-amendment", {}, "m")],
        [_record("conductor:execution-report", {"verdict": "pass", "revision": "r"}, "r")],
        [_record("tuner:check-run", {"result": "fail", "method": "tdd", "revision": "z"}, "c")],
    )
    assert [(e.kind, e.summary, e.revision) for e in entries] == [
        ("assignment", "assigned to inline", ""),
        ("assignment-amendment", "amended", ""),
        ("execution-report", "reported pass", "r"),
        ("check-run", "tdd check failed", "z"),
    ]


def test_timeline_entries_keep_unknown_check_results_and_trim_missing_method() -> None:
    (entry,) = timeline_entries([], [], [], [_record("tuner:check-run", {"result": "weird"})])
    assert entry.summary == "check weird"
