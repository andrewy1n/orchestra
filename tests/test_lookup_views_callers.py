from __future__ import annotations

from pathlib import Path

from canon_support import create, make_project

from dashboard.backend.journal import _phase_for_task
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.conductor.cli.workflow_commands import (
    _preview_json,
)
from orchestra.conductor.phase_progress import phase_counts as phase_progress
from orchestra.conductor.workflow import RunPreview
from orchestra.metrics.ops import tasks_of
from orchestra.metrics.phases import build_phase_rows
from orchestra.score.work_item_facts import owning_task_id


def _project(tmp_path: Path) -> Project:
    project = make_project(tmp_path / "repo")
    create(project, "score:effort", "alpha", {"goal": "Goal", "kind": "deliver"})
    return project


def _phase(project: Project, slug: str, depends_on: list[str] | None = None) -> Record:
    payload: JsonObject = {"title": slug, "ordinal": 1, "effort": "alpha", "weight": "light"}
    if depends_on is not None:
        payload["depends_on"] = list[JsonValue](depends_on)
    return create(project, "score:phase", slug, payload)


def _stored(project: Project, record_id: str) -> Record:
    return next(r for r in project.records() if r["id"] == record_id)


def _item(project: Project, subject: str, phase: str = "p1", **extra: JsonValue) -> Record:
    payload: JsonObject = {
        "title": subject,
        "phase": phase,
        "kind": "deliver",
        "assignee": "",
        "effort": "alpha",
        **extra,
    }
    return create(
        project,
        "score:work-item",
        subject,
        payload,
        "## Description\n\nDo.\n\n## Approach\n\nDo.",
    )


def test_r16_preview_prerequisites_come_from_the_current_phase_record(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "base")
    _phase(project, "other")
    current = _phase(project, "p1", depends_on=["base"])
    for index in range(6):
        target = "other" if index == 5 else "base"
        current = project.supersede(current["id"], payload={"depends_on": [target]})["record"]
    preview = RunPreview("alpha", "prepare", ("p1",), (), (), "token")

    result = _preview_json(project, preview)

    assert result["prerequisites"] == {"p1": ["other"]}


def test_r16_acceptance_owner_is_the_live_longest_subject_item(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1")
    foo = _item(project, "foo")
    old = _item(project, "foo-bar")
    new = project.supersede(old["id"], payload={"title": "again"})["record"]
    old = _stored(project, old["id"])

    assert owning_task_id("foo-bar-1", [old, new, foo]) == new["id"]
    assert owning_task_id("foo-1", [old, new, foo]) == foo["id"]
    assert owning_task_id("other-1", [old, new, foo]) == ""


def test_r16_journal_phase_for_task_uses_longest_live_subject(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1")
    _phase(project, "p2")
    foo = _item(project, "foo", phase="p1")
    old = _item(project, "foo-bar", phase="p2")
    new = project.supersede(old["id"], payload={"title": "again"})["record"]
    old = _stored(project, old["id"])

    assert _phase_for_task("foo-bar-1", [old, new, foo]) == ("p2", new["id"])
    assert _phase_for_task("foo-1", [old, new, foo]) == ("p1", foo["id"])


def test_r16_progress_counts_only_live_items_of_the_phase(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1")
    _phase(project, "p2")
    first = _item(project, "a")
    project.supersede(first["id"], payload={"title": "again"})
    _item(project, "b", phase="p2")

    progress = phase_progress(project.records(), "p1")

    assert progress.total == 1
    assert progress.counts["planned"] == 1


def test_r16_ops_tasks_follow_the_superseding_work_item(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1")
    first = _item(project, "a")
    new = project.supersede(first["id"], payload={"title": "again"})["record"]

    assert [t["id"] for t in tasks_of(project.records(), "p1")] == [new["id"]]


def test_r16_phase_metrics_report_a_superseded_done_phase_once(tmp_path: Path) -> None:
    project = _project(tmp_path)
    first = _phase(project, "p1")
    successor = project.supersede(first["id"], payload={"title": "again"})["record"]
    project.update(successor["id"], record_type="score:phase", transition="in_progress")
    project.update(successor["id"], record_type="score:phase", transition="done")

    rows = build_phase_rows(tmp_path / "repo")

    assert [r.phase for r in rows] == ["p1"]
