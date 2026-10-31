from __future__ import annotations

from typing import Any

import pytest

from orchestra.canon.backend import open_backend
from orchestra.canon.project import Project, open_store
from orchestra.canon.errors import StaleWriteError, StoreError
from conftest import make_task


def history_revisions(project: Project, record: dict[str, Any]) -> set[str]:
    return {
        snapshot["revision"]
        for snapshot in open_backend(project.store_path).read_history()
        if snapshot["id"] == record["id"]
    }


def test_open_store_returns_a_project(project, repo):
    assert isinstance(project, Project)
    assert project.store_path == (repo / ".canon").resolve()
    assert project.binding.location == "local"
    assert set(project.schemas().types) >= {"alpha:task", "beta:review"}


def test_get_and_list(project):
    task = make_task(project, "t")
    assert project.get(task["id"]) == task
    assert project.get(task["id"], "task") == task
    assert project.list("alpha:task") == [task]
    assert project.list("log") == []
    with pytest.raises(StoreError, match="is 'alpha:task', not 'alpha:log'"):
        project.get(task["id"], "log")
    with pytest.raises(StoreError, match="unknown record"):
        project.get("rec-00000000-0000-0000-0000-000000000000")


def test_resolve_returns_the_latest_record_of_a_subject(project):
    task = make_task(project, "t")
    successor = project.supersede(task["id"])["record"]
    assert project.resolve("task", "t")["id"] == successor["id"]
    with pytest.raises(StoreError, match="unknown record"):
        project.resolve("task", "ghost")


def test_update_archives_the_prior_revision(project):
    task = make_task(project, "t")
    assert history_revisions(project, task) == set()
    moved = project.update(task["id"], transition="in_progress")
    assert history_revisions(project, task) == {task["revision"]}
    project.update(task["id"], payload={"owner": "ann"})
    assert history_revisions(project, task) == {task["revision"], moved["revision"]}
    assert project.validate() == []


def test_supersede_archives_the_predecessor(project):
    task = make_task(project, "t")
    result = project.supersede(task["id"])
    assert history_revisions(project, task) == {task["revision"]}
    assert result["predecessor"]["revision"] != task["revision"]
    assert project.validate() == []


def test_events_are_archived_when_created(project):
    make_task(project, "t")
    log = project.create(record_type="alpha:log", subject="t", payload={"task": "t", "message": "m"})
    assert history_revisions(project, log) == {log["revision"]}


def test_stale_expected_revision_is_refused_and_changes_nothing(project):
    task = make_task(project, "t")
    project.update(task["id"], payload={"owner": "ann"})
    with pytest.raises(StaleWriteError):
        project.update(task["id"], payload={"owner": "bob"}, expected_revision=task["revision"])
    assert project.get(task["id"])["payload"]["owner"] == "ann"


def test_current_revision_is_the_default(project):
    task = make_task(project, "t")
    first = project.update(task["id"], payload={"owner": "ann"})
    second = project.update(task["id"], payload={"owner": "bob"})
    assert second["revision"] != first["revision"]
    assert project.update(task["id"], payload={"owner": "ann"}, expected_revision=second["revision"])


def test_update_with_no_revision_check_uses_none(project):
    task = make_task(project, "t")
    with pytest.raises(StoreError, match="expected revision required"):
        project.update(task["id"], payload={"owner": "ann"}, expected_revision=None)


def test_apply_numbers_results_by_operation(project):
    results = project.apply(
        [
            {"op": "create", "type": "alpha:task", "subject": "a", "payload": {"title": "a"}},
            {"op": "create", "type": "alpha:task", "subject": "b", "payload": {}},
            "oops",
            {"op": "update", "id": "rec-00000000-0000-0000-0000-000000000000"},
        ]
    )
    assert [r["line"] for r in results] == [1, 2, 3, 4]
    assert [r["ok"] for r in results] == [True, False, False, False]
    assert [r.get("error") for r in results] == [None, "validation", "store", "not_found"]


def test_supersede_failure_leaves_the_original_untouched(project):
    task = make_task(project, "t")
    with pytest.raises(Exception):
        project.supersede(task["id"], payload={"depends_on": ["ghost"]})
    assert project.get(task["id"]) == task


def test_chain_state_matches_the_materialized_record(project):
    from orchestra.canon import oplog

    task = make_task(project, "t")
    project.update(task["id"], payload={"owner": "ann"})
    chains = dict(open_backend(project.store_path).iter_chains())
    folded = oplog.fold(chains[task["id"]])
    assert folded == project.get(task["id"])


def test_open_store_after_init_in_a_subdirectory(project, repo):
    nested = repo / "a" / "b"
    nested.mkdir(parents=True)
    assert open_store(nested).store_path == project.store_path
