from __future__ import annotations

import itertools
import json

from orchestra.canon.types import JsonObject, Record
from orchestra.sessions.record_reader import read_records
from orchestra.views import STATUS, render_view

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
    assessment = _record(
        "conductor:assessment",
        "p",
        {"phase": "p", "requirement": "R1", "status": "unverified"},
        "active",
    )
    records = [
        _spec("p", "R1"),
        a1,
        _check_run(a1, "pass"),
        assessment,
        _work_item("t1", "p", "done"),
    ]
    out = _status(records)
    assert "- **R1**: unverified" in out
    assert f"assessment: {assessment['id']}" in out


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


def test_session_reader_assignee_from_work_item():
    item = _work_item("t1", "p", "in_progress", assignee="executor-a", write_root="/wt/t1")
    bare = _work_item("t2", "p", "planned")
    out = json.dumps({"records": [item, bare]})
    rows = read_records("/tmp/proj", types=["score:work-item"], run=lambda argv: out)
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


def test_session_reader_still_reads_written_assignment():
    item = _work_item("t1", "p", "in_progress")
    written = _record(
        "conductor:assignment",
        "t1",
        {"work_item": "t1", "executor": "legacy-exec", "write_root": "/wt/legacy"},
        "active",
    )
    by_type = {"score:work-item": [item], "conductor:assignment": [written]}

    def run(argv: list[str]) -> str:
        return json.dumps({"records": by_type.get(argv[argv.index("--type") + 1], [])})

    rows = [r for r in read_records("/tmp/proj", run=run) if r["record_type"] == "score:work-item"]
    assert rows[0].get("assignee") == "legacy-exec"
    assert rows[0].get("write_root") == "/wt/legacy"
