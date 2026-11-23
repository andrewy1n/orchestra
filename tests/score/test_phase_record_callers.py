from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from phase_record_support import supersede_all, supersede_late

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, Record
from orchestra.score.planning.requirements import phase_requirements, phase_weight
from orchestra.score.workflow.workflow_blockers import WorkflowBlockerError, phase_blockers
from orchestra.score.workflow.workflow_reviews import step_readiness
from orchestra.score.workflow.workflow_selection import PhaseSelectionError, resolve_phase_selection

PHASE = "feature"
EFFORT = "workflow"
BODY = "## Problem\nP.\n\n## Approach\nA.\n\n## Exit criteria\nE.\n"
LIGHT_BODY = BODY + "\n## Requirements\n\nR1: first\n"
FULL_BODY = BODY + "\n## Requirements\n\nR2: second\n"


def _payload(**extra: str) -> JsonObject:
    return {"title": "Feature", "ordinal": 1, "effort": EFFORT, **extra}


@pytest.fixture()
def project(store_template: Path, tmp_path: Path) -> Project:
    root = tmp_path / "repo"
    shutil.copytree(store_template, root)
    project = open_store(root)
    project.create(
        record_type="score:effort",
        subject=EFFORT,
        payload={"goal": "Deliver work", "kind": "deliver"},
    )
    return project


def _phase(project: Project, *, weight: str, body: str) -> Record:
    return project.create(
        record_type="score:phase",
        subject=PHASE,
        payload=_payload(weight=weight),
        body=body,
    )


def test_r13_phase_weight_ignores_superseded_phase(project: Project) -> None:
    phase = _phase(project, weight="light", body=LIGHT_BODY)
    supersede_late(project, phase, payload=_payload(weight="full"))

    assert phase_weight(project.records(), PHASE) == "full"


def test_r13_phase_requirements_read_current_phase(project: Project) -> None:
    phase = _phase(project, weight="light", body=LIGHT_BODY)
    supersede_late(project, phase, payload=_payload(weight="light"), body=FULL_BODY)

    assert phase_requirements(project.records(), PHASE) == [("R2", "second")]


def test_r13_all_superseded_phase_not_found(project: Project) -> None:
    phase = _phase(project, weight="light", body=LIGHT_BODY)
    supersede_all(project, phase, payload=_payload(weight="light"))
    records = project.records()

    assert phase_weight(records, PHASE) == "full"
    assert phase_requirements(records, PHASE) == []
    with pytest.raises(WorkflowBlockerError, match="phase 'feature' not found"):
        phase_blockers(records, PHASE)
    with pytest.raises(PhaseSelectionError):
        resolve_phase_selection(records, EFFORT, PHASE)
    assert step_readiness(records, PHASE, "tasks").status != "ready"


def test_r13_selection_reads_current_phase(project: Project) -> None:
    phase = _phase(project, weight="full", body=FULL_BODY)
    current, _ = supersede_late(project, phase, payload=_payload(weight="full"))

    selection = resolve_phase_selection(project.records(), EFFORT, PHASE)

    assert selection.dependency_order == (PHASE,)
    assert current["id"] != phase["id"]
