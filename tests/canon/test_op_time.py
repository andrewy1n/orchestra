from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from conftest import make_task

from orchestra.canon.backend import open_backend
from orchestra.canon.project import Project
from orchestra.canon.revision import with_revision
from orchestra.canon.types import Record, StoredOp

LEGACY_ID = "rec-6f1d7f5e-2c1a-4c55-9d0e-0a1b2c3d4e5f"


def _ops(project: Project, record_id: str) -> list[StoredOp]:
    return dict(open_backend(project.store_path).iter_chains())[record_id]


def _assert_utc_between(value: object, before: datetime, after: datetime) -> None:
    assert isinstance(value, str)
    parsed = datetime.fromisoformat(value)
    assert parsed.utcoffset() == timedelta(0)
    assert value.endswith("+00:00")
    assert before <= parsed <= after


def test_r1_create_operation_records_utc_time(project: Project) -> None:
    before = datetime.now(timezone.utc)
    task = make_task(project, "t")
    after = datetime.now(timezone.utc)
    (op,) = _ops(project, task["id"])
    assert op["kind"] == "create"
    _assert_utc_between(op.get("applied_at"), before, after)


def test_r2_update_operation_records_utc_time(project: Project) -> None:
    task = make_task(project, "t")
    before = datetime.now(timezone.utc)
    project.update(task["id"], transition="in_progress")
    after = datetime.now(timezone.utc)
    op = _ops(project, task["id"])[-1]
    assert op["kind"] == "write"
    _assert_utc_between(op.get("applied_at"), before, after)


def test_r2_supersede_operations_record_utc_time(project: Project) -> None:
    task = make_task(project, "t")
    before = datetime.now(timezone.utc)
    result = project.supersede(task["id"], payload={"title": "again"})
    after = datetime.now(timezone.utc)
    for record_id in (task["id"], result["record"]["id"]):
        _assert_utc_between(_ops(project, record_id)[-1].get("applied_at"), before, after)


def test_r3_delete_operation_records_utc_time(project: Project) -> None:
    task = make_task(project, "t")
    backend = open_backend(project.store_path)
    before = datetime.now(timezone.utc)
    backend.delete_record(task["record_type"], task["id"])
    after = datetime.now(timezone.utc)
    op = _ops(project, task["id"])[-1]
    assert op["kind"] == "delete"
    _assert_utc_between(op.get("applied_at"), before, after)


def _dump(project: Project) -> list[tuple[str, int, str]]:
    db = open_backend(project.store_path).db_path  # pyright: ignore[reportAttributeAccessIssue]
    with sqlite3.connect(db) as connection:
        return connection.execute("SELECT * FROM ops ORDER BY record_id, seq").fetchall()


def test_r7_opening_store_with_untimed_operations_changes_nothing(project: Project) -> None:
    seed = project.get(make_task(project, "seed")["id"])
    candidate: Record = {**seed, "id": LEGACY_ID, "subject": "legacy", "revision": ""}
    legacy = with_revision(candidate)
    backend = open_backend(project.store_path)
    op: StoredOp = {
        "seq": 1,
        "op_id": "legacy-op",
        "kind": "create",
        "outcome": "accepted",
        "record": legacy,
    }
    backend.import_op(legacy["record_type"], legacy["id"], op)
    backend.import_record(legacy)
    before = _dump(project)

    assert project.get(LEGACY_ID) == legacy
    assert len(project.records()) == 2
    assert project.validate() == []

    after = _dump(project)
    assert after == before
    assert "applied_at" not in _ops(project, LEGACY_ID)[0]
