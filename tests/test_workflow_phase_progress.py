from __future__ import annotations

from pathlib import Path

from canon_support import create, make_project
from conductor_support import write_policy

from orchestra.canon.project import Project
from orchestra.conductor.phases.progress import phase_progress
from orchestra.conductor.phases.workflow import workflow_review
from orchestra.conductor.phases.workflow.workflow import (
    RunAction,
    next_actions,
    preview_run,
    start_run,
)
from orchestra.score.planning.phase import current_phase_model
from orchestra.score.workflow.workflow_reviews import Step

EFFORT = "run-effort"
BODY = (
    "## Problem\nMeet the contract.\n"
    "## Requirements\nR1: Preserve workflow behavior.\n"
    "## Approach\nUse the reviewed design.\n"
    "## Exit criteria\nVerify the result.\n"
)


def _project(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    create(project, "score:effort", EFFORT, {"goal": "Workflow", "kind": "deliver"})
    return project


def _phase(project: Project, slug: str, ordinal: int, body: str = BODY) -> None:
    create(
        project,
        "score:phase",
        slug,
        {"title": slug, "ordinal": ordinal, "effort": EFFORT, "weight": "light"},
        body,
    )


def _review(project: Project, phase: str, step: Step) -> None:
    workflow_review.record_step_review(
        project,
        phase=phase,
        step=step,
        artifact=project.resolve("score:phase", phase),
        authority="user-approval",
        basis="Approved in the test fixture.",
    )


def _plan(project: Project, phase: str) -> None:
    create(
        project,
        "score:work-item",
        f"task-{phase}",
        {
            "title": "Task",
            "phase": phase,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "requirements": ["R1"],
        },
        "## Description\nImplement R1.",
    )
    create(
        project,
        "score:acceptance",
        f"acceptance-{phase}",
        {
            "method": "check",
            "phase": phase,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )


def _execution_report(project: Project, phase: str, result: str) -> None:
    task = project.resolve("score:work-item", f"task-{phase}")
    project.update(task["id"], record_type="score:work-item", transition="in_progress")
    project.update(task["id"], record_type="score:work-item", transition="done")
    create(
        project,
        "conductor:execution-report",
        task["subject"],
        {
            "work_item": task["subject"],
            "result": result,
            "verdict": result,
            "revision": "deadbeef",
            "effort": EFFORT,
        },
    )


def _passing_acceptance(project: Project, phase: str) -> None:
    acceptance = project.resolve("score:acceptance", f"acceptance-{phase}")
    create(
        project,
        "tuner:check-run",
        acceptance["subject"],
        {
            "criterion_id": acceptance["id"],
            "result": "pass",
            "revision": "deadbeef",
            "method": "check",
            "runner": "orchestra",
            "signed_by": "",
            "effort": EFFORT,
        },
    )


def _actions(
    project: Project, selector: str, operation: str, step: str | None = None
) -> tuple[RunAction, ...]:
    run = start_run(project, preview_run(project, EFFORT, selector, operation, step=step))
    return next_actions(project, run["subject"])


def _assessment_reason(project: Project, phase: str) -> str:
    records = project.records()
    model = current_phase_model(phase, records)
    assert model is not None
    return phase_progress.assess(phase_progress.phase_facts(project, records, model)).reason


def _only(actions: tuple[RunAction, ...]) -> RunAction:
    assert len(actions) == 1
    return actions[0]


def test_prepare_barrier_keeps_design_blocked_until_every_selected_spec_is_complete(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    _phase(project, "p2", 2)
    _review(project, "p1", "spec")

    actions = _actions(project, "p1,p2", "prepare")

    assert [(action.phase, action.step) for action in actions] == [("p2", "spec")]


def test_prepare_barrier_releases_design_for_every_phase_once_all_specs_complete(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    _phase(project, "p2", 2)
    _review(project, "p1", "spec")
    _review(project, "p2", "spec")

    actions = _actions(project, "p1,p2", "prepare")

    assert [(action.phase, action.step, action.state) for action in actions] == [
        ("p1", "design", "ready"),
        ("p2", "design", "ready"),
    ]


def test_prepare_barrier_does_not_hold_back_the_spec_of_a_phase_whose_design_is_done(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    _phase(project, "p2", 2)
    _review(project, "p1", "spec")
    _review(project, "p1", "design")

    actions = _actions(project, "p1,p2", "prepare")

    assert [(action.phase, action.step) for action in actions] == [("p2", "spec")]


def test_execute_reason_equals_the_assessment_reason_while_a_task_is_open(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    _plan(project, "p1")
    for step in ("spec", "design", "tasks"):
        _review(project, "p1", step)

    action = _only(_actions(project, "p1", "deliver"))

    assert (action.step, action.state) == ("execute", "ready")
    assert action.reason == _assessment_reason(project, "p1")
    assert action.reason == "task 'task-p1' is not done"


def test_execute_blocked_reason_equals_the_assessment_reason_after_a_failed_report(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    _plan(project, "p1")
    for step in ("spec", "design", "tasks"):
        _review(project, "p1", step)
    _execution_report(project, "p1", "fail")

    action = _only(_actions(project, "p1", "deliver"))

    assert (action.step, action.state) == ("execute", "blocked")
    assert action.reason == _assessment_reason(project, "p1")


def test_land_prerequisite_reason_carries_the_assessment_reason_of_verify(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    write_policy(project.project_root)
    _phase(project, "p1", 1, BODY + "## Landing\nBranch phase/p1.\n")
    _plan(project, "p1")
    for step in ("spec", "design", "tasks"):
        _review(project, "p1", step)
    _execution_report(project, "p1", "pass")
    _passing_acceptance(project, "p1")

    action = _only(_actions(project, "p1", "single-step", "land"))

    assert (action.step, action.state) == ("land", "blocked")
    assert _assessment_reason(project, "p1") == "reviewer"
    assert action.reason == "verify prerequisite is incomplete: reviewer"


def test_prerequisite_reason_names_the_first_open_stage_and_its_assessment_reason(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)

    action = _only(_actions(project, "p1", "single-step", "execute"))

    assert action.state == "blocked"
    assert action.reason == (
        f"spec prerequisite is incomplete: {_assessment_reason(project, 'p1')}"
    )
