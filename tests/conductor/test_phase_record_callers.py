from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from canon_support import create, make_project
from phase_record_support import supersede_all, supersede_late

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project, open_store
from orchestra.canon.types import Record
from orchestra.conductor import close, gate, workflow
from orchestra.conductor.tasks import land_task, wave
from orchestra.conductor.tasks.close import task_close
from orchestra.conductor.workflow_review import WorkflowReviewError, record_step_review

PHASE = "ph"
EFFORT = "ef"
BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n"


def _project(tmp_path: Path) -> tuple[Project, Record]:
    project = make_project(tmp_path)
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    phase = create(
        project, "score:phase", PHASE, {"title": "Ph", "ordinal": 1, "effort": EFFORT}, BODY
    )
    return project, phase


def _retired_project(tmp_path: Path) -> Project:
    project, phase = _project(tmp_path)
    supersede_all(project, phase, payload={"title": "Next", "ordinal": 1, "effort": EFFORT})
    return project


def test_r12_wave_ignores_superseded_phase(tmp_path: Path) -> None:
    project, phase = _project(tmp_path)
    current, _ = supersede_late(
        project, phase, payload={"title": "Next", "ordinal": 1, "effort": EFFORT}
    )

    assert wave.phase_record(project.records(), PHASE)["id"] == current["id"]


def test_r12_all_superseded_phase_not_found(tmp_path: Path) -> None:
    project = _retired_project(tmp_path)

    with pytest.raises(wave.WaveError, match="phase 'ph' not found"):
        wave.phase_record(project.records(), PHASE)


def test_r12_close_batch_all_superseded_phase_not_found(tmp_path: Path) -> None:
    project = _retired_project(tmp_path)

    with pytest.raises(LookupError, match="phase 'ph' not found"):
        task_close._phase_record(project, PHASE)


def test_r12_close_batch_reads_current_phase(tmp_path: Path) -> None:
    project, phase = _project(tmp_path)
    current, _ = supersede_late(
        project, phase, payload={"title": "Next", "ordinal": 1, "effort": EFFORT}
    )

    loaded = task_close._phase_record(project, PHASE)

    assert loaded["id"] == current["id"]


def test_r12_close_all_superseded_phase_not_found(tmp_path: Path) -> None:
    project = _retired_project(tmp_path)

    with pytest.raises(StoreError, match="unknown record: no score:phase with subject 'ph'"):
        close.pending_close(project, tmp_path, PHASE)


def _landed_task(project: Project, tmp_path: Path) -> tuple[land_task.LandedTask, Record]:
    item = project.create(
        record_type="score:work-item",
        subject="t",
        payload={
            "title": "t",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
        },
        body="## Description\n\nd\n\n## Approach\n\na",
    )
    acceptance = create(
        project,
        "score:acceptance",
        "t",
        {"method": "check", "phase": PHASE, "effort": EFFORT, "verify_command": "true"},
    )
    green = project.create(
        record_type="tuner:check-run",
        subject="t",
        payload={
            "criterion_id": acceptance["id"],
            "revision": "a" * 40,
            "result": "pass",
            "effort": EFFORT,
            "method": "check",
            "signed_by": "",
            "runner": "orchestra",
            "exit_code": 0,
        },
    )
    landed = land_task.LandedTask(
        task="t",
        phase=PHASE,
        commit="a" * 40,
        revision="a" * 40,
        report_id="",
        checks=(land_task.CheckResult(acceptance["id"], "t", green["id"], 0),),
        evidence_result="pass",
    )
    return landed, item


def test_r12_task_close_ignores_superseded_phase(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    phase = create(
        project,
        "score:phase",
        PHASE,
        {"title": "Ph", "ordinal": 1, "effort": EFFORT, "oracle_policy": "frozen"},
        BODY,
    )
    supersede_late(
        project,
        phase,
        payload={"title": "Next", "ordinal": 1, "effort": EFFORT, "oracle_policy": "none"},
    )
    landed, item = _landed_task(project, tmp_path)
    project.update(item["id"], record_type="score:work-item", transition="in_progress")

    assert task_close.close(project, replace(landed, verdict="pass"), frozenset()).state == "done"


def test_r13_workflow_all_superseded_phase_not_found(tmp_path: Path) -> None:
    project = _retired_project(tmp_path)

    with pytest.raises(workflow.WorkflowRunError, match="required phase 'ph' could not be read"):
        workflow._current_phase(project.records(), PHASE)


def test_r13_workflow_reads_current_phase(tmp_path: Path) -> None:
    project, phase = _project(tmp_path)
    current, _ = supersede_late(
        project, phase, payload={"title": "Next", "ordinal": 1, "effort": EFFORT}
    )

    assert workflow._current_phase(project.records(), PHASE).id == current["id"]


def test_r13_gate_all_superseded_phase_not_found(tmp_path: Path) -> None:
    project = _retired_project(tmp_path)

    with pytest.raises(LookupError, match="phase 'ph' not found"):
        gate.gate_terms(open_store(project.project_root), PHASE)


def test_r13_workflow_review_all_superseded_phase_not_found(tmp_path: Path) -> None:
    project, phase = _project(tmp_path)
    retired = supersede_all(
        project, phase, payload={"title": "Next", "ordinal": 1, "effort": EFFORT}
    )

    with pytest.raises(WorkflowReviewError, match="unknown phase 'ph'"):
        record_step_review(
            project, phase=PHASE, step="spec", artifact=retired[0], authority=None, basis=None
        )
