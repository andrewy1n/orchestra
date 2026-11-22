from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project
from phase_record_support import supersede_late

from dashboard.backend.phase import light_specification, load_phase_detail
from dashboard.backend.snapshot import PhaseRow, load_snapshot
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.metrics.phases import build_phase_rows
from orchestra.views.render import VIEWS, render_view

EFFORT = "workflow"
PHASE = "feature"
BODY = "## Problem\nP.\n\n## Approach\nA.\n\n## Exit criteria\nE.\n"
LIGHT_BODY = BODY + "\n## Requirements\n\nR1: stale\n"
FULL_BODY = BODY + "\n## Requirements\n\nR2: current\n"
STALE: JsonObject = {
    "title": "Stale title",
    "ordinal": 9,
    "effort": EFFORT,
    "weight": "light",
    "milestone": "old-milestone",
}
CURRENT: JsonObject = {
    "title": "Feature",
    "ordinal": 2,
    "effort": EFFORT,
    "weight": "full",
    "oracle_policy": "frozen",
    "milestone": "m1",
}


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    return tmp_path / "repo"


@pytest.fixture()
def project(root: Path) -> Project:
    project = make_project(root)
    create(project, "score:effort", EFFORT, {"goal": "Deliver work", "kind": "deliver"})
    for ordinal, (slug, title) in enumerate(
        (("old-milestone", "Old milestone"), ("m1", "Milestone one")), start=1
    ):
        create(
            project,
            "score:milestone",
            slug,
            {"title": title, "ordinal": ordinal, "effort": EFFORT},
        )
    stale = create(project, "score:phase", PHASE, STALE, LIGHT_BODY)
    current, _ = supersede_late(project, stale, payload=CURRENT, body=FULL_BODY)
    project.update(current["id"], record_type="score:phase", transition="in_progress")
    return project


def _snapshot_row(project: Project) -> PhaseRow:
    view = next(view for view in load_snapshot(project).efforts if view.effort == EFFORT)
    return next(row for row in view.phases if row.subject == PHASE)


def _current(project: Project) -> Record:
    return next(
        record
        for record in project.records()
        if record["record_type"] == "score:phase" and record["lifecycle_state"] != "superseded"
    )


def test_r2_snapshot_phase_row_reports_the_current_record(project: Project) -> None:
    row = _snapshot_row(project)

    assert (row.title, row.ordinal, row.milestone, row.milestone_title) == (
        "Feature",
        2,
        "m1",
        "Milestone one",
    )
    assert row.id == _current(project)["id"]
    assert row.evidence is None


def test_r2_phase_detail_reports_the_current_record(project: Project) -> None:
    detail = load_phase_detail(project, EFFORT, PHASE)

    assert detail.title == "Feature"
    assert detail.state == "in_progress"
    assert detail.milestone == "m1"
    assert detail.milestone_title == "Milestone one"
    assert detail.body == FULL_BODY
    assert detail.evidence is None


def test_r2_plan_view_and_snapshot_row_report_the_same_phase(project: Project) -> None:
    row = _snapshot_row(project)
    line = next(
        line
        for line in render_view(VIEWS["plan"], project.records()).splitlines()
        if line.startswith(f"- **{PHASE}**")
    )

    assert f"{row.title}; {row.ordinal}; {EFFORT}" in line


def test_r2_metrics_row_and_dashboard_report_the_current_weight_and_effort(
    project: Project, root: Path
) -> None:
    current = _current(project)
    project.update(current["id"], record_type="score:phase", transition="done")

    (metrics,) = build_phase_rows(root)
    row = _snapshot_row(project)
    detail = load_phase_detail(project, EFFORT, PHASE)

    assert (metrics.phase, metrics.effort, metrics.weight) == (PHASE, EFFORT, "full")
    assert (row.title, row.ordinal) == ("Feature", 2)
    assert detail.evidence is None
    assert detail.state == "done"


def test_r2_light_lookup_skips_a_superseded_light_phase(project: Project) -> None:
    assert light_specification(PHASE, EFFORT, project.records()) is None


def test_r2_light_lookup_reads_the_current_phase_body(project: Project) -> None:
    current = _current(project)
    project.supersede(
        current["id"],
        payload={**CURRENT, "weight": "light"},
        body=LIGHT_BODY.replace("stale", "again"),
    )

    spec = light_specification(PHASE, EFFORT, project.records())

    assert spec is not None
    assert spec["payload"]["requirements"] == ["R1"]
    assert spec.get("body", "").endswith("R1: again\n")
