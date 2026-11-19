from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra import views
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.metrics.phases import build_phase_rows
from orchestra.score.workflow_selection import resolve_phase_selection

LANDING: JsonObject = {
    "phase": "p1",
    "number": 7,
    "url": "u7",
    "head_sha": "abc123",
    "result": "success",
}
PACKET: JsonObject = {"phase": "p1", "revision": "abc123", "base": "main", "kind": "demo"}


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


def _handoff(project: Project) -> str:
    return views.render_view(views.VIEWS["handoff"], views.load_records(project))


def test_r11_handoff_names_merge_step_for_landing_without_effort(project: Project) -> None:
    _phase_state(project, "in_progress")
    _finish_tasks(project)
    create(project, "conductor:landing", "p1", LANDING)

    text = _handoff(project)

    assert "Awaiting merge: PR 7 (u7)" in text


def test_r11_handoff_names_packet_check_for_packet_without_effort(project: Project) -> None:
    _phase_state(project, "in_progress")
    _finish_tasks(project)
    packet: Record = {
        "id": "rec-packet",
        "record_type": "conductor:proof-packet",
        "subject": "p1",
        "payload": PACKET,
        "lifecycle_state": "recorded",
        "relationships": {},
        "revision": "sha256:x",
        "recorded_at": "2026-11-08T10:00:00+00:00",
        "body": "",
    }

    text = views.render_view(views.VIEWS["handoff"], [*views.load_records(project), packet])

    assert "verify the proof packet covers the phase head." in text
    assert "confirm landing" not in text


def test_r11_handoff_asks_for_packet_when_phase_has_no_optional_fields(project: Project) -> None:
    _phase_state(project, "in_progress")
    _finish_tasks(project)

    text = _handoff(project)

    assert "record the proof packet for any code or claim changes" in text


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
