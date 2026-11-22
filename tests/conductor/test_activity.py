from __future__ import annotations

from datetime import datetime, timezone

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.activity import ActivityEntry, activity_entries

SINCE = datetime(2026, 11, 1, 0, 0, 10, tzinfo=timezone.utc)
STAMP = "2026-11-01T00:00:{:02d}+00:00"


def _record(record_type: str, subject: str, payload: JsonObject, second: int) -> Record:
    return {
        "id": f"<{record_type}:{subject}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": f"r{second}",
        "recorded_at": STAMP.format(second),
    }


def _entry(
    kind: str, record: Record, summary: str, second: int, failed: bool = False
) -> ActivityEntry:
    return ActivityEntry(
        kind,
        record["id"],
        record["subject"],
        datetime(2026, 11, 1, 0, 0, second, tzinfo=timezone.utc),
        summary,
        failed,
    )


def test_assignment_names_the_work_item_subject_and_executor() -> None:
    record = _record("conductor:assignment", "assign", {"work_item": "<w1>", "executor": "sub"}, 20)
    found = activity_entries([record], [], [], {"<w1>": ("alpha", "task-one")}, SINCE)
    assert found == {"alpha": [_entry("assignment", record, "task-one assigned to sub", 20)]}


def test_assignment_effort_in_the_payload_wins_over_the_work_item_effort() -> None:
    record = _record(
        "conductor:assignment",
        "assign",
        {"work_item": "<w1>", "effort": "beta", "executor": "x"},
        20,
    )
    found = activity_entries([record], [], [], {"<w1>": ("alpha", "task-one")}, SINCE)
    assert list(found) == ["beta"]


def test_unknown_work_item_is_reported_by_reference_and_dropped_without_an_effort() -> None:
    record = _record("conductor:execution-report", "rep", {"work_item": "<w9>", "verdict": "x"}, 20)
    assert activity_entries([], [record], [], {}, SINCE) == {}
    assigned = _record("conductor:assignment", "a", {"work_item": "<w9>", "effort": "alpha"}, 20)
    found = activity_entries([assigned], [], [], {}, SINCE)
    assert found["alpha"][0].summary == "<w9> assigned to "


def test_report_fails_on_a_failing_result_or_verdict_only() -> None:
    reports = [
        _record("conductor:execution-report", "ok", {"work_item": "w", "verdict": "pass"}, 20),
        _record(
            "conductor:execution-report",
            "by-result",
            {"work_item": "w", "result": "fail", "verdict": "pass"},
            21,
        ),
        _record(
            "conductor:execution-report",
            "by-verdict",
            {"work_item": "w", "result": "pass", "verdict": "fail"},
            22,
        ),
    ]
    found = activity_entries([], reports, [], {"w": ("alpha", "task")}, SINCE)
    assert {(item.subject, item.failed) for item in found["alpha"]} == {
        ("ok", False),
        ("by-result", True),
        ("by-verdict", True),
    }
    assert found["alpha"][-1].summary == "task reported pass"


def test_check_run_label_names_the_method_and_outcome() -> None:
    passed = _record(
        "tuner:check-run", "c1", {"result": "pass", "method": "check", "effort": "a"}, 20
    )
    failed = _record(
        "tuner:check-run", "c2", {"result": "fail", "method": "manual", "effort": "a"}, 21
    )
    other = _record("tuner:check-run", "c3", {"result": "skipped", "effort": "a"}, 22)
    found = activity_entries([], [], [passed, failed, other], {}, SINCE)["a"]
    assert {item.subject: (item.summary, item.failed) for item in found} == {
        "c1": ("c1 check passed", False),
        "c2": ("c2 manual check failed", True),
        "c3": ("c3 check skipped", False),
    }


def test_entries_before_the_window_are_dropped_and_the_boundary_is_kept() -> None:
    old = _record("tuner:check-run", "old", {"result": "pass", "effort": "a"}, 9)
    edge = _record("tuner:check-run", "edge", {"result": "pass", "effort": "a"}, 10)
    found = activity_entries([], [], [old, edge], {}, SINCE)
    assert [item.subject for item in found["a"]] == ["edge"]


def test_entries_are_grouped_by_effort_and_sorted_newest_first() -> None:
    records = [
        _record("tuner:check-run", "first", {"result": "pass", "effort": "a"}, 20),
        _record("tuner:check-run", "third", {"result": "pass", "effort": "a"}, 40),
        _record("tuner:check-run", "second", {"result": "pass", "effort": "a"}, 30),
        _record("tuner:check-run", "other", {"result": "pass", "effort": "b"}, 25),
    ]
    found = activity_entries([], [], records, {}, SINCE)
    assert [item.subject for item in found["a"]] == ["third", "second", "first"]
    assert [item.subject for item in found["b"]] == ["other"]


def test_assessment_integration_and_release_need_a_structured_phase() -> None:
    assessment = _record(
        "conductor:assessment",
        "as",
        {"effort": "a", "phase": "p", "requirement": "R1", "status": "failed", "next": "plan"},
        20,
    )
    integration = _record(
        "conductor:integration-report",
        "int",
        {"effort": "a", "phase": "p", "result": "blocked"},
        21,
    )
    release = _record(
        "conductor:release", "rel", {"effort": "a", "phase": "p", "state": "failed"}, 22
    )
    args = ([], [], [], {}, SINCE, [assessment], [integration], [release])
    assert activity_entries(*args) == {}
    assert activity_entries(*args, {("a", "other")}) == {}
    found = activity_entries(*args, {("a", "p")})["a"]
    assert {item.kind: (item.summary, item.failed) for item in found} == {
        "assessment": ("R1 failed plan upstream", True),
        "integration": ("p blocked", True),
        "release": ("p failed", True),
    }


def test_integration_and_release_pass_states_are_not_failures() -> None:
    integration = _record(
        "conductor:integration-report", "int", {"effort": "a", "phase": "p", "result": "pass"}, 21
    )
    release = _record(
        "conductor:release", "rel", {"effort": "a", "phase": "p", "state": "ready"}, 22
    )
    found = activity_entries([], [], [], {}, SINCE, None, [integration], [release], {("a", "p")})
    assert [(item.kind, item.failed) for item in found["a"]] == [
        ("release", False),
        ("integration", False),
    ]


def test_assessment_level_change_reads_the_superseded_assessment() -> None:
    old = _record("conductor:assessment", "as", {"effort": "a", "phase": "p", "level": "design"}, 5)
    new = _record(
        "conductor:assessment",
        "as",
        {"effort": "a", "phase": "p", "requirement": "R1", "status": "x", "level": "code"},
        20,
    )
    new["id"] = "<new>"
    new["relationships"] = {"supersedes": [old["id"]]}
    found = activity_entries([], [], [], {}, SINCE, [old, new], None, None, {("a", "p")})["a"]
    assert [item.summary for item in found] == ["R1 x  level design to code"]
