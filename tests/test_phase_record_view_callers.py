from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject
from orchestra.conductor.phases.progress.phase_progress import open_phase_progress
from orchestra.metrics.phases import build_phase_rows
from orchestra.score.workflow.workflow_selection import resolve_phase_selection
from orchestra.views import render as views

LANDING: JsonObject = {
    "phase": "p1",
    "number": 7,
    "url": "u7",
    "head_sha": "abc123",
    "result": "success",
}


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = make_project(tmp_path / "repo")
    seed_effort(project, "alpha")
    return project


def _finish_tasks(project: Project) -> None:
    task = create(
        project,
        "score:work-item",
        "build-it",
        {"title": "Build", "phase": "p1", "kind": "deliver", "assignee": "", "effort": "alpha"},
    )
    project.update(task["id"], transition="in_progress")
    project.update(task["id"], transition="done")


def _phase_state(project: Project, *transitions: str) -> None:
    phase = project.resolve("score:phase", "p1")
    for transition in transitions:
        project.update(phase["id"], transition=transition)


def test_r11_handoff_names_a_stage_for_a_phase_without_optional_fields(project: Project) -> None:
    _phase_state(project, "in_progress")
    _finish_tasks(project)
    records = views.load_records(project)

    text = views.render_view(
        views.VIEWS["handoff"], records, progress=open_phase_progress(project, records)
    )

    assert "stage: spec" in text


def test_r11_metrics_row_reports_missing_weight_and_reads_landing_without_effort(
    project: Project,
) -> None:
    _finish_tasks(project)
    _phase_state(project, "in_progress", "done")
    create(project, "conductor:landing", "p1", LANDING)

    (row,) = build_phase_rows(project.project_root)

    assert row.weight is None
    assert row.missing["weight"] == "the phase record has no weight"
    assert row.landing_source == "conductor:landing"
    assert row.landing_time is not None


def test_r11_workflow_selection_reads_phase_without_optional_fields(project: Project) -> None:
    selection = resolve_phase_selection(project.records(), "alpha", "p1")

    assert selection.dependency_order == ("p1",)
