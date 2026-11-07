from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from conftest import copy_store

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import get_object
from orchestra.canon.validation import ValidationError


@pytest.fixture()
def project(store_template: Path, tmp_path: Path) -> Project:
    root = copy_store(store_template)
    target = tmp_path / "repo"
    shutil.copytree(root, target, dirs_exist_ok=True)
    shutil.rmtree(root)
    return open_store(target)


def _effort(project: Project, subject: str) -> str:
    return project.create(
        record_type="score:effort",
        subject=subject,
        payload={"goal": "Workflow", "kind": "deliver"},
    )["subject"]


def _phase(project: Project, effort: str, subject: str) -> str:
    return project.create(
        record_type="score:phase",
        subject=subject,
        payload={"title": subject, "ordinal": 1, "effort": effort},
        body="## Problem\nNeed workflow records.\n## Approach\nAdd them.\n## Exit criteria\nResume a run.",
    )["subject"]


def test_workflow_records_persist_and_legacy_work_items_remain_valid(project: Project) -> None:
    effort = _effort(project, "workflow")
    phase = _phase(project, effort, "playbooks")
    artifact = project.create(
        record_type="score:acceptance",
        subject="reviewed-contract",
        payload={"method": "check", "effort": effort, "verify_command": "true"},
    )
    review = project.create(
        record_type="score:step-review",
        subject="design-review",
        payload={
            "effort": effort,
            "phase": phase,
            "step": "design",
            "reviewed_artifact": artifact["id"],
            "reviewed_revision": artifact["revision"],
            "input_fingerprint": "inputs-v1",
            "source_reviews": [],
            "authority": "user-approval",
            "basis": "Approved after review.",
        },
    )
    run = project.create(
        record_type="score:run",
        subject="run-1",
        payload={
            "effort": effort,
            "operation": "deliver",
            "phases": [phase],
            "requested_steps": ["execute", "verify"],
            "definition_version": "1",
        },
    )
    legacy_task = project.create(
        record_type="score:work-item",
        subject="legacy-task",
        payload={
            "title": "Existing task",
            "kind": "deliver",
            "assignee": "parent",
            "effort": effort,
        },
        body="## Description\nExisting work item.",
    )

    assert project.get(review["id"])["payload"]["source_reviews"] == []
    assert project.get(run["id"])["payload"]["phases"] == [phase]
    assert "source_reviews" not in legacy_task["payload"]


def test_workflow_review_rejects_phase_from_another_effort(project: Project) -> None:
    effort = _effort(project, "workflow-a")
    other_effort = _effort(project, "workflow-b")
    phase = _phase(project, effort, "phase-a")
    artifact = project.create(
        record_type="score:acceptance",
        subject="contract-a",
        payload={"method": "check", "effort": effort, "verify_command": "true"},
    )

    with pytest.raises(ValidationError, match="belongs to a different effort"):
        project.create(
            record_type="score:step-review",
            subject="bad-review",
            payload={
                "effort": other_effort,
                "phase": phase,
                "step": "design",
                "reviewed_artifact": artifact["id"],
                "reviewed_revision": artifact["revision"],
                "input_fingerprint": "inputs-v1",
                "source_reviews": [],
                "authority": "explicit-delegation",
                "basis": "Delegated.",
            },
        )


def test_workflow_schemas_expose_optional_progress_fields(project: Project) -> None:
    schemas = project.schemas()

    score_types = get_object(schemas.modules["score"], "types")
    assert score_types is not None
    assert "step-review" in score_types
    assert "run" in score_types
    assert "source_reviews" in schemas.types["score:work-item"].fields
    assert "phase" in schemas.types["tuner:finding"].fields
