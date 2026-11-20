from __future__ import annotations

from conftest import advance, make_task

from orchestra.canon.backend import open_backend
from orchestra.canon.derive import attach_derived_all
from orchestra.canon.project import Project
from orchestra.canon.revision import compute_revision
from orchestra.canon.types import Record


def _write_order(record: Record) -> int:
    return record.get("derived", {}).get("write_order", -1)


def test_write_order_increases_in_creation_order(project: Project) -> None:
    created = [make_task(project, name) for name in ("c", "a", "b")]
    by_id = {record["id"]: record for record in project.records()}
    orders = [_write_order(by_id[record["id"]]) for record in created]
    assert orders == sorted(orders)
    assert len(set(orders)) == len(orders)


def test_write_order_of_a_record_does_not_change_when_it_is_updated(project: Project) -> None:
    first = make_task(project, "first")
    second = make_task(project, "second")
    before = {r["id"]: _write_order(r) for r in project.records()}
    advance(project, first, "in_progress")
    after = {r["id"]: _write_order(r) for r in project.records()}
    assert after == before
    assert after[first["id"]] < after[second["id"]]


def test_write_order_is_absent_from_the_stored_record(project: Project) -> None:
    task = make_task(project, "t")
    stored = open_backend(project.store_path).read_record(task["record_type"], task["id"])
    assert "derived" not in stored
    assert "write_order" not in stored
    assert "write_order" not in str(stored)


def test_write_order_leaves_the_revision_unchanged(project: Project) -> None:
    task = make_task(project, "t")
    (read,) = project.records()
    stored = open_backend(project.store_path).read_record(task["record_type"], task["id"])
    assert read["revision"] == task["revision"] == stored["revision"]
    assert compute_revision(stored) == stored["revision"]


def test_write_order_sits_beside_other_derived_values(project: Project) -> None:
    make_task(project, "a")
    b = make_task(project, "b", depends_on=["a"])
    by_id = {r["id"]: r for r in project.records()}
    derived = project.derived(list(by_id.values()))
    merged = {r["id"]: r for r in attach_derived_all(list(by_id.values()), derived)}
    assert merged[b["id"]].get("derived", {}).get("ready") is False
    assert _write_order(merged[b["id"]]) > 0


def test_cli_get_and_list_show_write_order_only_under_derived(project: Project, cli) -> None:
    task = make_task(project, "t")
    got = cli.ok("get", "--id", task["id"])
    listed = cli.ok("list", "--type", "alpha:task")
    assert got["derived"]["write_order"] >= 1
    assert "write_order" not in {key for key in got if key != "derived"}
    assert listed["records"][0]["derived"]["write_order"] == got["derived"]["write_order"]
