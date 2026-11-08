from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.workflow_review import record_step_review
from orchestra.score.analyze import analyze_phase
from orchestra.score.workflow_reviews import (
    Authority,
    Step,
    light_phase_fingerprints,
    step_readiness,
)


@pytest.fixture()
def project(store_template: Path, tmp_path: Path) -> Project:
    root = tmp_path / "repo"
    shutil.copytree(store_template, root)
    return open_store(root)


def _effort(project: Project, subject: str = "workflow") -> str:
    return project.create(
        record_type="score:effort",
        subject=subject,
        payload={"goal": "Workflow", "kind": "deliver", "autonomy": "auto-plan"},
    )["subject"]


def _phase(project: Project, effort: str, subject: str = "phase", *, light: bool = False) -> Record:
    payload: JsonObject = {"title": subject, "ordinal": 1, "effort": effort}
    if light:
        payload["weight"] = "light"
    return project.create(
        record_type="score:phase",
        subject=subject,
        payload=payload,
        body=(
            "## Problem\nMeet the contract.\n"
            "## Approach\nUse the selected design.\n"
            "## Exit criteria\nVerify the result.\n"
            "## Landing\nUse a phase worktree.\n"
        ),
    )


def _spec(project: Project, effort: str, phase: str, subject: str = "spec") -> Record:
    return project.create(
        record_type="score:specification",
        subject=subject,
        payload={"weight": "full", "phase": phase, "effort": effort, "requirements": ["R1"]},
        body=(
            "## Requirements\nR1: Preserve the workflow contract.\n"
            "## Acceptance criteria\nR1 passes.\n"
            "## Constraints\nKeep scope fixed.\n"
            "## Non-goals\nNo unrelated changes.\n"
            "## Invariants\nApproval remains explicit.\n"
            "## Assumptions\nThe store is available.\n"
        ),
    )


def _design(project: Project, effort: str, phase: str, subject: str = "design") -> Record:
    return project.create(
        record_type="score:design",
        subject=subject,
        payload={"phase": phase, "effort": effort, "decisions": []},
        body=(
            "## Architecture\nUse workflow records.\n"
            "## Interfaces\nUse typed APIs.\n"
            "## Decisions\nPersist reviews.\n"
            "## Invariants\nDo not infer approval.\n"
            "## Assumptions\nThe phase exists.\n"
            "## Tradeoffs\nKeep writes atomic.\n"
            "## Risks\nStale inputs need review.\n"
        ),
    )


def _review(
    project: Project,
    phase: str,
    step: Step,
    artifact: Record,
    authority: Authority,
    basis: str,
    source_reviews: list[Record] | None = None,
) -> Record:
    return record_step_review(
        project,
        phase=phase,
        step=step,
        artifact=artifact,
        authority=authority,
        basis=basis,
        source_reviews=source_reviews or [],
    )


def test_blocking_behavior_question_prevents_spec_readiness(project: Project) -> None:
    effort = _effort(project)
    _phase(project, effort)
    specification = _spec(project, effort, "phase")
    review = _review(project, "phase", "spec", specification, "user-approval", "Approved.")
    project.create(
        record_type="score:continuity-question",
        subject="behavior-question",
        payload={
            "owner": "user",
            "blocking": True,
            "scope": "specification",
            "phase": "phase",
            "question": "Which behavior should the workflow use?",
        },
    )

    assert review["payload"]["authority"] == "user-approval"
    assert step_readiness(project.records(), "phase", "spec").status == "blocked"


def test_review_authority_preserves_user_and_delegated_sources(project: Project) -> None:
    effort = _effort(project)
    _phase(project, effort)
    specification = _spec(project, effort, "phase")
    user_review = _review(
        project, "phase", "spec", specification, "user-approval", "User approved."
    )
    design = _design(project, effort, "phase")
    delegated_review = _review(
        project,
        "phase",
        "design",
        design,
        "explicit-delegation",
        "User delegated the design decision.",
        [user_review],
    )

    assert user_review["payload"]["basis"] == "User approved."
    assert delegated_review["payload"]["authority"] == "explicit-delegation"
    assert delegated_review["payload"]["basis"] == "User delegated the design decision."


def test_light_phase_tracks_contract_approach_and_proof_separately(project: Project) -> None:
    effort = _effort(project)
    phase = _phase(project, effort, light=True)
    body = phase.get("body")
    assert isinstance(body, str)
    original = light_phase_fingerprints(body)
    changed_approach = light_phase_fingerprints(
        body.replace("Use the selected design.", "Use another design.")
    )
    changed_operations = light_phase_fingerprints(
        body.replace("Use a phase worktree.", "Use a different worktree.")
    )

    assert changed_approach.contract == original.contract
    assert changed_approach.approach != original.approach
    assert changed_approach.proof == original.proof
    assert changed_operations == original


def test_upstream_change_marks_affected_outputs_stale(project: Project) -> None:
    effort = _effort(project)
    _phase(project, effort, "phase-a")
    _phase(project, effort, "phase-b")
    specification = _spec(project, effort, "phase-a", "spec-a")
    unaffected_spec = _spec(project, effort, "phase-b", "spec-b")
    spec_review = _review(project, "phase-a", "spec", specification, "user-approval", "Approved.")
    unaffected_review = _review(
        project, "phase-b", "spec", unaffected_spec, "user-approval", "Approved."
    )
    design = _design(project, effort, "phase-a", "design-a")
    _review(project, "phase-a", "design", design, "user-approval", "Approved.", [spec_review])
    project.update(
        specification["id"],
        payload={"requirements": ["R2"]},
        body=(
            "## Requirements\nR2: Changed requirement.\n"
            "## Acceptance criteria\nR2 passes.\n"
            "## Constraints\nKeep scope fixed.\n"
            "## Non-goals\nNo unrelated changes.\n"
            "## Invariants\nApproval remains explicit.\n"
            "## Assumptions\nThe store is available.\n"
        ),
    )

    assert step_readiness(project.records(), "phase-a", "design").status == "stale"
    assert step_readiness(project.records(), "phase-b", "spec").review == unaffected_review


def test_approval_or_explicit_delegation_establishes_readiness(project: Project) -> None:
    effort = _effort(project)
    _phase(project, effort)
    specification = _spec(project, effort, "phase")

    assert step_readiness(project.records(), "phase", "spec").status == "missing"
    user_review = _review(project, "phase", "spec", specification, "user-approval", "Approved.")

    assert step_readiness(project.records(), "phase", "spec").review == user_review
    project.update(
        specification["id"],
        payload={"requirements": ["R2"]},
        body=(
            "## Requirements\nR2: Preserve the workflow contract.\n"
            "## Acceptance criteria\nR2 passes.\n"
            "## Constraints\nKeep scope fixed.\n"
            "## Non-goals\nNo unrelated changes.\n"
            "## Invariants\nApproval remains explicit.\n"
            "## Assumptions\nThe store is available.\n"
        ),
    )
    delegated_review = _review(
        project,
        "phase",
        "spec",
        project.get(specification["id"]),
        "explicit-delegation",
        "User delegated readiness.",
    )

    assert delegated_review["payload"]["authority"] == "explicit-delegation"
    assert step_readiness(project.records(), "phase", "spec").review == delegated_review


def test_spec_analysis_does_not_require_task_coverage(project: Project) -> None:
    effort = _effort(project)
    _phase(project, effort)
    _spec(project, effort, "phase")

    report = analyze_phase(project.records(), "phase", stage="spec")

    assert report.ok


def test_plan_analysis_keeps_task_coverage_requirements(project: Project) -> None:
    effort = _effort(project)
    _phase(project, effort)
    _spec(project, effort, "phase")

    report = analyze_phase(project.records(), "phase")

    assert {finding.code for finding in report.findings} >= {
        "requirement-no-work-item",
        "requirement-no-acceptance",
    }


def test_unchanged_review_is_reused_without_new_approval(project: Project) -> None:
    effort = _effort(project)
    _phase(project, effort)
    specification = _spec(project, effort, "phase")
    review = _review(project, "phase", "spec", specification, "user-approval", "Approved.")
    before = project.records()

    reused = record_step_review(
        project,
        phase="phase",
        step="spec",
        artifact=specification,
        authority=None,
        basis=None,
    )

    assert reused["id"] == review["id"]
    assert project.records() == before


def test_task_review_ignores_execution_state_but_tracks_plan_changes(project: Project) -> None:
    effort = _effort(project)
    phase = _phase(project, effort)
    specification = _spec(project, effort, "phase")
    spec_review = _review(project, "phase", "spec", specification, "user-approval", "Approved.")
    design = _design(project, effort, "phase")
    design_review = _review(
        project, "phase", "design", design, "user-approval", "Approved.", [spec_review]
    )
    work_item = project.create(
        record_type="score:work-item",
        subject="task-a",
        payload={
            "title": "Implement workflow",
            "phase": "phase",
            "kind": "deliver",
            "assignee": "parent",
            "effort": effort,
            "requirements": ["R1"],
        },
        body="## Description\nImplement the approved workflow.",
    )
    _review(
        project,
        "phase",
        "tasks",
        phase,
        "task-plan-policy",
        "workflow-loop auto-plan policy",
        [spec_review, design_review],
    )

    project.update(work_item["id"], transition="in_progress")
    assert step_readiness(project.records(), "phase", "tasks").status == "ready"

    project.update(work_item["id"], payload={"title": "Changed task plan"})
    assert step_readiness(project.records(), "phase", "tasks").status == "stale"
