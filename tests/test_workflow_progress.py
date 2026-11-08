from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.errors import StaleWriteError
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor import workflow_review
from orchestra.conductor.workflow import (
    WorkflowRunError,
    next_actions,
    preview_run,
    run_status,
    start_run,
)
from orchestra.score.workflow_reviews import Authority, Step

EFFORT = "run-effort"
PHASE_BODY = (
    "## Problem\nMeet the contract.\n"
    "## Requirements\nR1: Preserve workflow behavior.\n"
    "## Approach\nUse the reviewed design.\n"
    "## Exit criteria\nVerify the result.\n"
)


def _project(tmp_path: Path, *, autonomy: str = "gated") -> Project:
    project = make_project(tmp_path)
    create(
        project,
        "score:effort",
        EFFORT,
        {"goal": "Workflow", "kind": "deliver", "autonomy": autonomy},
    )
    return project


def _phase(
    project: Project, slug: str, ordinal: int, *, dependencies: list[str] | None = None
) -> Record:
    payload: dict[str, object] = {
        "title": slug,
        "ordinal": ordinal,
        "effort": EFFORT,
        "weight": "light",
    }
    if dependencies is not None:
        payload["depends_on"] = dependencies
    return create(project, "score:phase", slug, payload, PHASE_BODY)


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


def _review(
    project: Project,
    phase: str,
    step: Step,
    authority: Authority = "user-approval",
) -> None:
    artifact = project.resolve("score:phase", phase)
    workflow_review.record_step_review(
        project,
        phase=phase,
        step=step,
        artifact=artifact,
        authority=authority,
        basis="Approved in the test fixture.",
    )


def _ready_through_tasks(project: Project, phase: str) -> None:
    _plan(project, phase)
    _review(project, phase, "spec")
    _review(project, phase, "design")
    _review(project, phase, "tasks")


def _start(project: Project, selector: str, operation: str, *, step: str | None = None) -> Record:
    preview = preview_run(project, EFFORT, selector, operation, step=step)
    return start_run(project, preview)


def test_prepare_waits_for_all_selected_specifications(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    _phase(project, "p2", 2)
    _review(project, "p1", "spec")
    run = _start(project, "p1,p2", "prepare")

    actions = next_actions(project, run["subject"])

    assert [(action.phase, action.step) for action in actions] == [("p2", "spec")]


def test_prepare_does_not_wait_for_selected_dependency_to_finish(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    _phase(project, "p2", 2, dependencies=["p1"])
    _review(project, "p1", "spec")
    _review(project, "p2", "spec")
    run = _start(project, "p1,p2", "prepare")

    actions = next_actions(project, run["subject"])

    assert [(action.phase, action.step, action.state) for action in actions] == [
        ("p1", "design", "ready"),
        ("p2", "design", "ready"),
    ]


def test_tasks_action_is_ready_before_work_items_exist(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    _review(project, "p1", "spec")
    _review(project, "p1", "design")
    run = _start(project, "p1", "phase")

    actions = next_actions(project, run["subject"])

    assert [(action.step, action.state) for action in actions] == [("tasks", "ready")]


def test_single_step_run_never_advances_to_another_step(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    _review(project, "p1", "spec")
    run = _start(project, "p1", "single-step", step="design")

    actions = next_actions(project, run["subject"])

    assert [(action.phase, action.step) for action in actions] == [("p1", "design")]


def test_external_prerequisite_is_reported_without_scope_expansion(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "prerequisite", 1)
    _phase(project, "selected", 2, dependencies=["prerequisite"])
    run = _start(project, "selected", "phase")

    actions = next_actions(project, run["subject"])

    assert run["payload"]["phases"] == ["selected"]
    assert len(actions) == 1
    assert actions[0].state == "blocked"
    assert "prerequisite" in actions[0].reason


def test_resume_uses_first_unfinished_valid_step(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    run = _start(project, "p1", "phase")
    _review(project, "p1", "spec")

    status = run_status(project, run["subject"])

    assert status.incomplete is True
    assert [(action.phase, action.step) for action in status.actions] == [("p1", "design")]


def test_existing_approval_and_autonomy_rules_apply(tmp_path: Path) -> None:
    project = _project(tmp_path, autonomy="gated")
    _phase(project, "p1", 1)
    _plan(project, "p1")
    _review(project, "p1", "spec")
    _review(project, "p1", "design")
    with pytest.raises(workflow_review.WorkflowReviewError, match="does not permit"):
        _review(project, "p1", "tasks", authority="task-plan-policy")
    run = _start(project, "p1", "deliver")

    actions = next_actions(project, run["subject"])

    assert [(action.step, action.state) for action in actions] == [("tasks", "ready")]


def test_policy_review_reads_autonomy_from_the_active_effort_record(tmp_path: Path) -> None:
    project = _project(tmp_path, autonomy="gated")
    effort = project.resolve("score:effort", EFFORT)
    project.supersede(effort["id"], payload={"autonomy": "auto-phases"})
    _phase(project, "p1", 1)
    _plan(project, "p1")
    _review(project, "p1", "spec")
    _review(project, "p1", "design")
    _review(project, "p1", "tasks", authority="task-plan-policy")
    run = _start(project, "p1", "deliver")

    actions = next_actions(project, run["subject"])

    assert [(action.step, action.state) for action in actions] == [("execute", "ready")]


def test_starting_run_does_not_grant_merge_approval(tmp_path: Path) -> None:
    project = _project(tmp_path)
    phase = _phase(project, "p1", 1)

    run = _start(project, "p1", "phase")

    assert run["record_type"] == "score:run"
    assert project.get(phase["id"])["lifecycle_state"] == "planned"
    assert not [r for r in project.records() if r["record_type"] == "score:step-review"]


def test_required_read_and_check_failures_remain_failures(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    _ready_through_tasks(project, "p1")
    task = project.resolve("score:work-item", "task-p1")
    project.update(task["id"], record_type="score:work-item", transition="in_progress")
    project.update(task["id"], record_type="score:work-item", transition="done")
    create(
        project,
        "conductor:execution-report",
        "task-p1",
        {
            "work_item": task["subject"],
            "result": "fail",
            "verdict": "fail",
            "revision": "deadbeef",
            "effort": EFFORT,
        },
    )
    run = _start(project, "p1", "phase")

    actions = next_actions(project, run["subject"])

    assert actions[0].step == "execute"
    assert actions[0].state == "blocked"
    assert "fail" in actions[0].reason
    with pytest.raises(WorkflowRunError, match="missing"):
        next_actions(project, "missing-run")


def test_serial_phase_verification_does_not_require_integration_report(tmp_path: Path) -> None:
    project = _project(tmp_path)
    phase = _phase(project, "p1", 1)
    _ready_through_tasks(project, "p1")
    task = project.resolve("score:work-item", "task-p1")
    acceptance = project.resolve("score:acceptance", "acceptance-p1")
    project.update(task["id"], record_type="score:work-item", transition="in_progress")
    project.update(task["id"], record_type="score:work-item", transition="done")
    create(
        project,
        "conductor:execution-report",
        "task-p1",
        {
            "work_item": task["subject"],
            "result": "pass",
            "verdict": "pass",
            "revision": "deadbeef",
            "effort": EFFORT,
        },
    )
    create(
        project,
        "tuner:check-run",
        "acceptance-p1",
        {
            "criterion_id": acceptance["id"],
            "result": "pass",
            "revision": "deadbeef",
            "method": "check",
            "signed_by": "",
            "effort": EFFORT,
        },
    )
    project.update(phase["id"], record_type="score:phase", transition="in_progress")
    project.update(phase["id"], record_type="score:phase", transition="done")
    run = _start(project, "p1", "phase")

    status = run_status(project, run["subject"])

    assert status.complete is True


def test_parallel_implementation_wave_needs_integration_report_at_verification(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    phase = _phase(project, "p1", 1)
    _review(project, "p1", "spec")
    _review(project, "p1", "design")
    for subject in ("task-a", "task-b"):
        create(
            project,
            "score:work-item",
            subject,
            {
                "title": subject,
                "phase": "p1",
                "kind": "deliver",
                "assignee": "",
                "effort": EFFORT,
                "requirements": ["R1"],
            },
            "## Description\nImplement R1.",
        )
    acceptance = create(
        project,
        "score:acceptance",
        "acceptance-p1",
        {
            "method": "check",
            "phase": "p1",
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    _review(project, "p1", "tasks")
    for subject in ("task-a", "task-b"):
        task = project.resolve("score:work-item", subject)
        project.update(task["id"], record_type="score:work-item", transition="in_progress")
        project.update(task["id"], record_type="score:work-item", transition="done")
        create(
            project,
            "conductor:execution-report",
            subject,
            {
                "work_item": subject,
                "result": "pass",
                "verdict": "pass",
                "revision": "deadbeef",
                "effort": EFFORT,
            },
        )
    create(
        project,
        "tuner:check-run",
        "acceptance-p1",
        {
            "criterion_id": acceptance["id"],
            "result": "pass",
            "revision": "deadbeef",
            "method": "check",
            "signed_by": "",
            "effort": EFFORT,
        },
    )
    run = _start(project, "p1", "phase")

    action = next_actions(project, run["subject"])[0]
    assert (action.step, action.state) == ("verify", "ready")
    project.update(phase["id"], record_type="score:phase", transition="in_progress")
    project.update(phase["id"], record_type="score:phase", transition="done")
    assert run_status(project, run["subject"]).complete is False

    create(
        project,
        "conductor:integration-report",
        "p1-integration",
        {"phase": "p1", "effort": EFFORT, "result": "pass", "revision": "deadbeef"},
        "## Interfaces\nReviewed.\n## Assumptions\nReviewed.\n"
        "## Invariants\nReviewed.\n## Conflicts\nNone.",
    )

    assert run_status(project, run["subject"]).complete is True


def test_any_unfinished_required_step_keeps_run_incomplete(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    run = _start(project, "p1", "phase")

    status = run_status(project, run["subject"])

    assert status.incomplete is True
    assert status.complete is False


def test_unknown_custom_playbook_is_rejected_before_writes(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1)
    before = project.records()

    with pytest.raises(WorkflowRunError, match="unsupported"):
        preview_run(project, EFFORT, "p1", "custom-playbook")

    assert project.records() == before


def test_start_run_rejects_a_changed_preview_snapshot(tmp_path: Path) -> None:
    project = _project(tmp_path)
    phase = _phase(project, "p1", 1)
    preview = preview_run(project, EFFORT, "p1", "phase")
    project.update(phase["id"], record_type="score:phase", body=PHASE_BODY + "\nChanged.")

    with pytest.raises(StaleWriteError, match="changed since the snapshot"):
        start_run(project, preview)
