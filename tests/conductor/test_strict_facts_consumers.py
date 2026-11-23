from __future__ import annotations

import pytest

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.signoff import awaiting_signoff
from orchestra.conductor.task_detail import related_text, timeline_entries
from orchestra.conductor.verification.suite.suite_label import suite_labels, suite_status_label
from orchestra.tuner.evidence.record_facts import RecordShapeError

REQUIRED = ("criterion_id", "revision", "result", "method", "signed_by")


def _record(
    record_type: str, subject: str, payload: JsonObject, record_id: str, state: str = "recorded"
) -> Record:
    return {
        "id": record_id,
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00Z",
    }


def _check(subject: str, drop: str | None = None, **override: str | int) -> Record:
    payload: JsonObject = {
        "criterion_id": "<acc:1>",
        "revision": "abcdef0123",
        "result": "pass",
        "method": "manual",
        "signed_by": "",
        "effort": "e",
        "evidence_kind": "integration",
    }
    payload.update(override)
    if drop:
        del payload[drop]
    return _record("tuner:check-run", subject, payload, "<cr:bad>")


def _phase_inputs() -> tuple[list[Record], list[Record]]:
    task = _record("score:work-item", "t", {"phase": "p", "effort": "e"}, "<wi:t>", "planned")
    return [task], [task]


@pytest.mark.parametrize("field", REQUIRED)
def test_signoff_reports_a_check_run_missing_a_required_field(field: str) -> None:
    members, items = _phase_inputs()
    with pytest.raises(RecordShapeError) as caught:
        awaiting_signoff("active", members, items, [], [_check("t-acc", drop=field)])
    assert (caught.value.record_id, caught.value.field) == ("<cr:bad>", field)


def test_signoff_does_not_read_a_missing_signed_by_as_unsigned() -> None:
    members, items = _phase_inputs()
    acceptance = _record(
        "score:acceptance",
        "t-acc",
        {"phase": "p", "effort": "e", "method": "manual", "criterion": "c"},
        "<acc:1>",
        "active",
    )
    with pytest.raises(RecordShapeError):
        awaiting_signoff("active", members, items, [acceptance], [_check("t-acc", "signed_by")])


def test_signoff_still_reads_an_empty_signed_by_as_unsigned() -> None:
    members, items = _phase_inputs()
    acceptance = _record(
        "score:acceptance",
        "t-acc",
        {"phase": "p", "effort": "e", "method": "manual", "criterion": "c"},
        "<acc:1>",
        "active",
    )
    assert awaiting_signoff("active", members, items, [acceptance], [_check("t-acc")])


@pytest.mark.parametrize("field", ["revision", "result"])
def test_suite_label_reports_a_check_run_missing_a_field_it_prints(field: str) -> None:
    with pytest.raises(RecordShapeError) as caught:
        suite_status_label("p", [_check("p-suite", drop=field)])
    assert (caught.value.record_id, caught.value.field) == ("<cr:bad>", field)


def test_suite_label_does_not_print_a_placeholder_for_a_missing_revision() -> None:
    with pytest.raises(RecordShapeError):
        suite_status_label("p", [_check("p-suite", drop="revision")])


def test_suite_label_reports_a_malformed_legacy_check_run() -> None:
    legacy = _check("p-tier2", drop="result")
    with pytest.raises(RecordShapeError):
        suite_labels([legacy])


def test_suite_label_unchanged_for_a_valid_check_run() -> None:
    assert suite_status_label("p", [_check("p-suite")]) == "suite ok@abcdef0"


@pytest.mark.parametrize("field", ["method", "result", "revision"])
def test_timeline_reports_a_check_run_missing_a_field_it_shows(field: str) -> None:
    with pytest.raises(RecordShapeError) as caught:
        timeline_entries([], [], [], [_check("t", drop=field)])
    assert (caught.value.record_id, caught.value.field) == ("<cr:bad>", field)


def test_timeline_unchanged_for_a_valid_check_run() -> None:
    entries = timeline_entries([], [], [], [_check("t")])
    assert [(e.summary, e.revision) for e in entries] == [("manual check passed", "abcdef0123")]


def test_related_text_reports_a_finding_missing_a_required_field() -> None:
    finding = _record("tuner:finding", "t", {"claim": "c", "basis": "b"}, "<f:bad>", "active")
    with pytest.raises(RecordShapeError) as caught:
        related_text(finding)
    assert (caught.value.record_id, caught.value.field) == ("<f:bad>", "needs")
