from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.score.workflow_selection import PhaseSelectionError, resolve_phase_selection


@pytest.fixture()
def project(store_template: Path, tmp_path: Path) -> Project:
    root = tmp_path / "repo"
    shutil.copytree(store_template, root)
    return open_store(root)


def _effort(project: Project, subject: str) -> None:
    project.create(
        record_type="score:effort",
        subject=subject,
        payload={"goal": "Workflow", "kind": "deliver"},
    )


def _phase(
    project: Project,
    effort: str,
    subject: str,
    ordinal: int,
    depends_on: list[str] | None = None,
) -> Record:
    payload: JsonObject = {
        "title": subject,
        "ordinal": ordinal,
        "effort": effort,
    }
    if depends_on is not None:
        dependencies: list[JsonValue] = []
        dependencies.extend(depends_on)
        payload["depends_on"] = dependencies
    return project.create(
        record_type="score:phase",
        subject=subject,
        payload=payload,
        body="## Problem\nPlan work.\n## Approach\nRun phases.\n## Exit criteria\nComplete work.",
    )


def test_selectors_resolve_within_one_effort(project: Project) -> None:
    _effort(project, "first")
    _effort(project, "second")
    _phase(project, "first", "alpha", 1)
    _phase(project, "first", "beta", 2)
    _phase(project, "first", "gamma", 3)
    _phase(project, "second", "other", 1)

    result = resolve_phase_selection(project.records(), "first", "alpha,2,2-3")

    assert result.effort["subject"] == "first"
    assert result.phase_subjects == ("alpha", "beta", "gamma")
    assert result.dependency_order == ("alpha", "beta", "gamma")


def test_invalid_selection_has_no_writes(project: Project) -> None:
    _effort(project, "first")
    _phase(project, "first", "alpha", 1)
    before = project.records()

    with pytest.raises(PhaseSelectionError):
        resolve_phase_selection(before, "first", "1-3")

    assert project.records() == before


def test_dependency_order_and_cycles(project: Project) -> None:
    _effort(project, "first")
    _phase(project, "first", "foundation", 2)
    _phase(project, "first", "delivery", 1, ["foundation"])

    result = resolve_phase_selection(project.records(), "first", "delivery")

    assert result.phase_subjects == ("delivery",)
    assert result.dependency_order == ("delivery",)
    assert result.external_dependencies == ("foundation",)

    cycle_a = _phase(project, "first", "cycle-a", 3)
    _phase(project, "first", "cycle-b", 4, ["cycle-a"])
    project.update(cycle_a["id"], payload={"depends_on": ["cycle-b"]})

    with pytest.raises(PhaseSelectionError, match="cycle"):
        resolve_phase_selection(project.records(), "first", "cycle-a,cycle-b")
