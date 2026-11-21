from __future__ import annotations

from datetime import datetime, timezone
from itertools import permutations
from pathlib import Path

from canon_support import create, make_project

from dashboard.backend.records import newest_record
from dashboard.backend.task import task_rows
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.evidence_recovery import recover_evidence
from orchestra.conductor.requirements import requirement_status

STAMP = "2026-01-01T00:00:00+00:00"
LATER = "2026-01-02T00:00:00+00:00"


def _record(
    record_id: str,
    record_type: str,
    subject: str,
    payload: JsonObject,
    *,
    state: str = "active",
    recorded_at: str = STAMP,
) -> Record:
    return {
        "id": record_id,
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": record_id,
        "recorded_at": recorded_at,
    }


def _item(
    record_id: str, subject: str, state: str, *, derived: bool = False, recorded_at: str = STAMP
) -> Record:
    record = _record(
        record_id,
        "score:work-item",
        subject,
        {"phase": "p1", "effort": "alpha"},
        state=state,
        recorded_at=recorded_at,
    )
    if derived:
        record["derived"] = {"ready": True}
    return record


def test_newest_record_breaks_equal_stamps_by_write_order_in_both_orders() -> None:
    first = _record("b-2", "tuner:check-run", "x", {})
    second = _record("a-1", "tuner:check-run", "x", {})
    first["derived"] = {"write_order": 1}
    second["derived"] = {"write_order": 2}
    assert newest_record([first, second]) == second
    assert newest_record([second, first]) == second


def test_requirement_status_picks_the_same_assessment_in_both_orders() -> None:
    phase = _record("ph", "score:phase", "p1", {"effort": "alpha", "weight": "full"})
    spec = _record("sp", "score:specification", "p1-spec", {"phase": "p1", "requirements": ["r1"]})
    failed = _record(
        "as-1",
        "conductor:assessment",
        "p1-r1",
        {"phase": "p1", "requirement": "r1", "status": "failed"},
    )
    unverified = _record(
        "as-2",
        "conductor:assessment",
        "p1-r1",
        {"phase": "p1", "requirement": "r1", "status": "unverified"},
    )
    for pair in permutations([failed, unverified]):
        status = requirement_status([phase, spec, *pair], "p1")["r1"]
        assert status.assessment_id == "as-2"


def test_dashboard_task_owns_acceptance_of_superseded_nested_sibling() -> None:
    foo = _item("w-foo", "foo", "in_progress")
    bar = _item("w-bar", "foo-bar", "superseded")
    assignment = _record(
        "as", "conductor:assignment", "foo-a", {"work_item": "foo"}, recorded_at=STAMP
    )
    check = _record(
        "ck",
        "tuner:check-run",
        "foo-bar-x",
        {"criterion_id": "acc"},
        recorded_at=LATER,
    )
    rows = task_rows([foo, bar], [assignment], checks=[check])
    assert rows[0].last_record_at == datetime(2026, 1, 2, tzinfo=timezone.utc)


def test_dashboard_task_leaves_acceptance_of_live_nested_item_to_it() -> None:
    foo = _item("w-foo", "foo", "in_progress")
    bar = _item("w-bar", "foo-bar", "planned")
    assignment = _record("as", "conductor:assignment", "foo-a", {"work_item": "foo"})
    check = _record(
        "ck", "tuner:check-run", "foo-bar-x", {"criterion_id": "acc"}, recorded_at=LATER
    )
    rows = {row.subject: row for row in task_rows([foo, bar], [assignment], checks=[check])}
    assert rows["foo"].last_record_at == datetime(2026, 1, 1, tzinfo=timezone.utc)


def _work_item(project: Project, subject: str) -> Record:
    return create(
        project,
        "score:work-item",
        subject,
        {"title": subject, "phase": "p1", "kind": "deliver", "assignee": "", "effort": "alpha"},
        "## Description\n\nDo.\n\n## Approach\n\nDo.",
    )


def _recovery_bucket(tmp_path: Path) -> str:
    project = make_project(tmp_path / "repo")
    create(project, "score:effort", "alpha", {"goal": "Goal", "kind": "deliver"})
    create(project, "score:phase", "p1", {"title": "p1", "ordinal": 1, "effort": "alpha"})
    _work_item(project, "foo")
    first = _work_item(project, "foo-bar")
    successor = project.supersede(first["id"], payload={"title": "again"})["record"]
    project.update(successor["id"], transition="in_progress")
    project.update(successor["id"], transition="done")
    acceptance = create(
        project,
        "score:acceptance",
        "foo-bar-x",
        {"phase": "p1", "effort": "alpha", "method": "tdd", "verify_command": "true"},
    )
    report = recover_evidence(project)
    return next(
        name
        for name in ("historical", "fresh_proof_required", "recoverable")
        if acceptance["id"] in report[name]  # pyright: ignore[reportTypedDictNotRequiredAccess]
    )


def test_evidence_recovery_gives_nested_acceptance_to_the_longest_subject(tmp_path: Path) -> None:
    assert _recovery_bucket(tmp_path) == "historical"
