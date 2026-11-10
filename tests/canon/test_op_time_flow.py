from __future__ import annotations

import io
from pathlib import Path

from conftest import Cli, make_task

from orchestra.canon.backend import open_backend
from orchestra.canon.project import Project
from orchestra.canon.revision import with_revision
from orchestra.canon.sqlite_backend import SqliteBackend
from orchestra.canon.transfer import export_ops, import_ops
from orchestra.canon.types import Record, StoredOp

UNTIMED_ID = "rec-6f1d7f5e-2c1a-4c55-9d0e-0a1b2c3d4e5f"


def _insert_untimed_record(project: Project) -> None:
    seed = project.get(make_task(project, "seed")["id"])
    candidate: Record = {**seed, "id": UNTIMED_ID, "subject": "untimed", "revision": ""}
    untimed = with_revision(candidate)
    op: StoredOp = {
        "seq": 1,
        "op_id": "untimed-op",
        "kind": "create",
        "outcome": "accepted",
        "record": untimed,
    }
    backend = open_backend(project.store_path)
    backend.import_op(untimed["record_type"], untimed["id"], op)
    backend.import_record(untimed)


def test_r8_export_then_import_keeps_each_time_and_absence(
    project: Project, tmp_path: Path
) -> None:
    task = make_task(project, "timed")
    project.update(task["id"], transition="in_progress")
    _insert_untimed_record(project)
    source = open_backend(project.store_path)

    dump = io.StringIO()
    export_ops(source, dump)
    target = SqliteBackend(tmp_path / "metadata", tmp_path / "data")
    import_ops(target, io.StringIO(dump.getvalue()))

    source_chains = dict(source.iter_chains())
    assert dict(target.iter_chains()) == source_chains
    assert all("applied_at" in op for op in source_chains[task["id"]])
    assert all("applied_at" not in op for op in source_chains[UNTIMED_ID])
    assert [entry["applied_at"] for entry in project.history(task["id"])] == [
        op.get("applied_at") for op in source_chains[task["id"]]
    ]


def test_r9_cli_create_then_update_shows_increasing_history_times(
    cli: Cli, project: Project
) -> None:
    created = cli(
        "create", "--type", "alpha:task", "--subject", "flow", "--payload", '{"title": "flow"}'
    )
    assert created.code == 0
    record_id = created.json["record"]["id"]
    cli.ok(
        "update",
        "--type",
        "alpha:task",
        "--id",
        record_id,
        "--transition",
        "in_progress",
        "--expected-revision",
        "@current",
    )

    history = project.history(record_id)
    assert [entry["lifecycle_state"] for entry in history] == ["planned", "in_progress"]
    first, second = (entry["applied_at"] for entry in history)
    assert first is not None
    assert second is not None
    assert first < second
