from __future__ import annotations

import itertools
from pathlib import Path

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, Record
from orchestra.sessions.record_reader import read_project_records
from orchestra.views import STATUS, VERIFICATION, render_view

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


def _check_run(acceptance: Record, result: str) -> Record:
    return _record(
        "tuner:check-run",
        acceptance["subject"],
        {"criterion_id": acceptance["id"], "result": result, "revision": "abc"},
    )


def _work_item(subject: str, phase: str, state: str, **payload: str) -> Record:
    return _record("score:work-item", subject, {"phase": phase, **payload}, state)


def _status(records: list[Record]) -> str:
    return render_view(STATUS, records)


def _store_project(store: Path) -> Project:
    project = open_store(store)
    project.create(
        record_type="score:effort", subject="e", payload={"goal": "g", "kind": "deliver"}
    )
    project.create(
        record_type="score:phase",
        subject="p",
        payload={"effort": "e", "title": "p", "ordinal": 1},
        body="## Problem\nOne\n## Approach\nTwo\n## Exit criteria\nThree",
    )
    return project


def _store_work_item(project: Project, subject: str, **extra: str) -> Record:
    payload: JsonObject = {
        "title": subject,
        "phase": "p",
        "kind": "deliver",
        "assignee": "",
        "effort": "e",
    }
    payload.update(extra)
    return project.create(
        record_type="score:work-item", subject=subject, payload=payload, body="## Description\nD"
    )


def test_views_show_derived_verified_status():
    a1 = _acceptance("a1", "p", "R1")
    a2 = _acceptance("a2", "p", "R2")
    records = [
        _spec("p", "R1", "R2"),
        a1,
        a2,
        _check_run(a1, "pass"),
        _check_run(a2, "fail"),
        _work_item("t1", "p", "done"),
    ]
    out = _status(records)
    assert "- **R1**: verified" in out
    assert "- **R2**: failed" in out
    assert "- not ready" in out


def test_views_show_release_ready_when_every_requirement_verified():
    a1 = _acceptance("a1", "p", "R1")
    records = [_spec("p", "R1"), a1, _check_run(a1, "pass"), _work_item("t1", "p", "done")]
    out = _status(records)
    assert "### Release\n- ready" in out


def test_views_written_non_verified_assessment_wins_over_derivation():
    a1 = _acceptance("a1", "p", "R1")
    run = _check_run(a1, "pass")
    assessment = _record(
        "conductor:assessment",
        "p",
        {"phase": "p", "requirement": "R1", "status": "unverified"},
        "active",
    )
    records = [_spec("p", "R1"), a1, run, assessment, _work_item("t1", "p", "done")]
    out = _status(records)
    assert "- **R1**: unverified" in out
    assert f"assessment: {assessment['id']}" in out


def test_verification_view_shows_derived_status():
    a1 = _acceptance("a1", "p", "R1")
    a2 = _acceptance("a2", "p", "R2")
    records = [
        _spec("p", "R1", "R2"),
        a1,
        a2,
        _check_run(a1, "pass"),
        _check_run(a2, "fail"),
    ]
    out = render_view(VERIFICATION, records)
    assert "- **R1**: verified" in out
    assert "- **R2**: failed" in out
    assert "### Release\n- not ready" in out


def test_views_show_written_assessment_status_name():
    a1 = _acceptance("a1", "p", "R1")
    a2 = _acceptance("a2", "p", "R2")
    a3 = _acceptance("a3", "p", "R3")
    records = [
        _spec("p", "R1", "R2", "R3"),
        a1,
        a2,
        a3,
        _check_run(a1, "pass"),
        _check_run(a2, "pass"),
        _check_run(a3, "pass"),
        _work_item("t1", "p", "done"),
    ]
    for requirement, status in (("R1", "failed"), ("R2", "blocked"), ("R3", "insufficient")):
        records.append(
            _record(
                "conductor:assessment",
                "p",
                {"phase": "p", "requirement": requirement, "status": status},
                "active",
            )
        )
    for view in (STATUS, VERIFICATION):
        out = render_view(view, records)
        assert "- **R1**: failed" in out
        assert "- **R2**: blocked" in out
        assert "- **R3**: insufficient" in out


def test_views_derivation_scoped_to_effort():
    a1 = _record(
        "score:acceptance", "a1", {"phase": "p", "requirement": "R1", "effort": "e1"}, "active"
    )
    a2 = _record(
        "score:acceptance", "a2", {"phase": "p", "requirement": "R1", "effort": "e2"}, "active"
    )
    spec1 = _record(
        "score:specification",
        "p-spec-1",
        {"phase": "p", "requirements": ["R1"], "effort": "e1"},
        "active",
    )
    spec2 = _record(
        "score:specification",
        "p-spec-2",
        {"phase": "p", "requirements": ["R1"], "effort": "e2"},
        "active",
    )
    records = [
        spec1,
        spec2,
        a1,
        a2,
        _check_run(a1, "pass"),
        _work_item("t1", "p", "done", effort="e1"),
        _work_item("t2", "p", "planned", effort="e2"),
        _work_item("t3", "p", "planned", effort="e2"),
    ]
    e1 = render_view(STATUS, records, effort="e1")
    e2 = render_view(STATUS, records, effort="e2")
    assert "- 1/1 done" in e1
    assert "- **R1**: verified" in e1
    assert "- 0/2 done" in e2
    assert "- **R1**: unverified" in e2


def test_views_phase_progress_derived():
    records = [
        _work_item("t1", "p", "done"),
        _work_item("t2", "p", "in_progress"),
        _work_item("t3", "p", "planned"),
        _work_item("t4", "other", "done"),
    ]
    out = _status(records)
    assert "- 1/3 done (planned: 1, in_progress: 1, done: 1)" in out
    assert "- in progress: t2" in out


def test_session_reader_assignee_from_work_item(store: Path):
    project = _store_project(store)
    _store_work_item(project, "t1", assignee="executor-a", write_root="/wt/t1")
    _store_work_item(project, "t2")
    rows = read_project_records(project, ["score:work-item"])
    by_subject = {r["subject"]: r for r in rows}
    assert by_subject["t1"].get("assignee") == "executor-a"
    assert by_subject["t1"].get("write_root") == "/wt/t1"
    assert "assignee" not in by_subject["t2"]
    assert "write_root" not in by_subject["t2"]


def test_views_assignee_and_write_root_from_work_item():
    item = _work_item("t1", "p", "in_progress", assignee="executor-a", write_root="/wt/t1")
    out = _status([item])
    assert "assignee: executor-a" in out
    assert "write root: /wt/t1" in out


def test_views_still_read_written_assignment():
    item = _work_item("t1", "p", "in_progress")
    written = _record(
        "conductor:assignment",
        "t1",
        {"work_item": "t1", "assignee": "legacy-exec", "write_root": "/wt/legacy"},
        "active",
    )
    out = _status([item, written])
    assert "assignee: legacy-exec" in out
    assert "write root: /wt/legacy" in out


def test_session_reader_still_reads_written_assignment(store: Path):
    project = _store_project(store)
    _store_work_item(project, "t1")
    project.create(
        record_type="conductor:assignment",
        subject="t1",
        payload={"work_item": "t1", "executor": "legacy-exec", "effort": "e"},
        body="## Orientation\nO",
    )
    rows = [r for r in read_project_records(project) if r["record_type"] == "score:work-item"]
    assert rows[0].get("assignee") == "legacy-exec"
