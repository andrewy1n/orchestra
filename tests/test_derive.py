from __future__ import annotations

import itertools

from orchestra.canon.types import JsonObject, Record
from orchestra.derive import (
    phase_progress,
    release_ready,
    requirement_status,
    task_assignment,
)

_CLOCK = itertools.count()


def _record(record_type: str, subject: str, payload: JsonObject, state: str = "recorded") -> Record:
    n = next(_CLOCK)
    return {
        "id": f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:00:{n:02d}Z",
    }


def _spec(phase: str, *requirements: str) -> Record:
    return _record(
        "score:specification",
        f"{phase}-spec",
        {"phase": phase, "requirements": list(requirements)},
        "active",
    )


def _acceptance(subject: str, phase: str, requirement: str) -> Record:
    return _record(
        "score:acceptance", subject, {"phase": phase, "requirement": requirement}, "active"
    )


def _check_run(acceptance: Record, result: str, revision: str = "abc") -> Record:
    return _record(
        "tuner:check-run",
        acceptance["subject"],
        {"criterion_id": acceptance["id"], "result": result, "revision": revision},
    )


def _work_item(subject: str, phase: str, state: str, **payload: str) -> Record:
    return _record("score:work-item", subject, {"phase": phase, **payload}, state)


def _assessment(phase: str, requirement: str, status: str) -> Record:
    return _record(
        "conductor:assessment",
        phase,
        {"phase": phase, "requirement": requirement, "status": status},
        "active",
    )


def test_requirement_status_verified_from_passing_check_runs():
    a1 = _acceptance("a1", "p", "R1")
    a2 = _acceptance("a2", "p", "R1")
    runs = [_check_run(a1, "fail"), _check_run(a1, "pass"), _check_run(a2, "pass")]
    statuses = requirement_status([_spec("p", "R1"), a1, a2, *runs], "p")
    assert statuses["R1"].status == "verified"
    assert statuses["R1"].acceptance_ids == (a1["id"], a2["id"])
    assert statuses["R1"].check_run_ids == (runs[1]["id"], runs[2]["id"])


def test_requirement_status_failed_and_unverified():
    a1 = _acceptance("a1", "p", "R1")
    a2 = _acceptance("a2", "p", "R2")
    a3 = _acceptance("a3", "p", "R3")
    records = [
        _spec("p", "R1", "R2", "R3", "R4"),
        a1,
        a2,
        a3,
        _check_run(a1, "pass"),
        _check_run(a1, "fail"),
        _check_run(a2, "pass"),
    ]
    statuses = requirement_status(records, "p")
    assert {k: v.status for k, v in statuses.items()} == {
        "R1": "failed",
        "R2": "verified",
        "R3": "unverified",
        "R4": "unverified",
    }


def test_requirement_status_partial_acceptances_stay_unverified():
    a1 = _acceptance("a1", "p", "R1")
    a2 = _acceptance("a2", "p", "R1")
    statuses = requirement_status([_spec("p", "R1"), a1, a2, _check_run(a1, "pass")], "p")
    assert statuses["R1"].status == "unverified"


def test_requirement_status_without_specification_uses_work_item_requirements():
    item = _record("score:work-item", "t", {"phase": "p", "requirements": ["R7"]}, "done")
    other = _record("score:work-item", "u", {"phase": "q", "requirements": ["R8"]}, "done")
    assert list(requirement_status([item, other], "p")) == ["R7"]


def test_requirement_status_respects_head():
    a1 = _acceptance("a1", "p", "R1")
    records = [_spec("p", "R1"), a1, _check_run(a1, "pass", revision="old")]
    assert requirement_status(records, "p")["R1"].status == "verified"
    assert requirement_status(records, "p", head="old")["R1"].status == "verified"
    assert requirement_status(records, "p", head="new")["R1"].status == "unverified"
    records.append(_check_run(a1, "pass", revision="new"))
    assert requirement_status(records, "p", head="new")["R1"].status == "verified"


def test_written_non_verified_assessment_wins():
    a1 = _acceptance("a1", "p", "R1")
    a2 = _acceptance("a2", "p", "R2")
    records = [
        _spec("p", "R1", "R2"),
        a1,
        a2,
        _check_run(a1, "pass"),
        _check_run(a2, "pass"),
        _assessment("p", "R1", "blocked"),
        _assessment("p", "R2", "verified"),
    ]
    statuses = requirement_status(records, "p")
    assert statuses["R1"].status == "unverified"
    assert statuses["R1"].assessment_id is not None
    assert statuses["R2"].status == "verified"
    assert statuses["R2"].assessment_id is None
    assert not release_ready(records, "p")


def test_stale_non_verified_assessment_yields_to_newer_passes():
    a1 = _acceptance("a1", "p", "R1")
    a2 = _acceptance("a2", "p", "R1")
    records = [_spec("p", "R1"), a1, a2, _check_run(a1, "pass")]
    assessment = _assessment("p", "R1", "blocked")
    records.append(assessment)
    assert requirement_status(records, "p")["R1"].assessment_id == assessment["id"]
    records.append(_check_run(a2, "pass"))
    assert requirement_status(records, "p")["R1"].assessment_id == assessment["id"]
    records.append(_check_run(a1, "pass"))
    status = requirement_status(records, "p")["R1"]
    assert status.status == "verified"
    assert status.assessment_id is None
    assert release_ready(records, "p")


def test_stale_assessment_with_newer_failure_still_wins():
    a1 = _acceptance("a1", "p", "R1")
    assessment = _assessment("p", "R1", "insufficient")
    records = [_spec("p", "R1"), a1, assessment, _check_run(a1, "pass"), _check_run(a1, "fail")]
    status = requirement_status(records, "p")["R1"]
    assert status.assessment_id == assessment["id"]
    assert status.assessed == "insufficient"


def test_release_ready():
    a1 = _acceptance("a1", "p", "R1")
    a2 = _acceptance("a2", "p", "R2")
    records = [_spec("p", "R1", "R2"), a1, a2, _check_run(a1, "pass")]
    assert not release_ready(records, "p")
    records.append(_check_run(a2, "pass"))
    assert release_ready(records, "p")
    assert not release_ready(records, "p", head="other")
    assert not release_ready([], "p")


def test_phase_progress_counts_states():
    records = [
        _work_item("a", "p", "done"),
        _work_item("b", "p", "in_progress"),
        _work_item("c", "p", "in_progress"),
        _work_item("d", "p", "planned"),
        _work_item("e", "p", "withdrawn"),
        _work_item("f", "q", "done"),
    ]
    progress = phase_progress(records, "p")
    assert progress.counts == {"planned": 1, "in_progress": 2, "done": 1}
    assert (progress.done, progress.total) == (1, 4)
    assert progress.in_progress == ("b", "c")


def test_task_assignment_from_work_item():
    item = _work_item("t", "p", "in_progress", assignee="agent-1", write_root="/w/t")
    written = _record("conductor:assignment", "t-a1", {"work_item": "t", "executor": "subagent"})
    assignment = task_assignment(item, [item, written])
    assert assignment is not None
    assert (assignment.assignee, assignment.write_root) == ("agent-1", "/w/t")


def test_task_assignment_falls_back_to_written_assignment():
    item = _work_item("t", "p", "in_progress", assignee="")
    older = _record("conductor:assignment", "t-a1", {"work_item": "t", "executor": "inline"})
    newer = _record(
        "conductor:assignment",
        "t-a2",
        {"work_item": "t", "executor": "subagent", "write_root": "/w/t"},
    )
    unrelated = _record("conductor:assignment", "u-a1", {"work_item": "u", "executor": "x"})
    assignment = task_assignment(item, [item, older, newer, unrelated])
    assert assignment is not None
    assert (assignment.assignee, assignment.write_root) == ("subagent", "/w/t")
    assert task_assignment(item, [item, unrelated]) is None
