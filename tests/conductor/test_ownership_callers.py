from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project
from test_wave_end import PHASE, _land, _world

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import Record
from orchestra.conductor import gate, land_task, phase_progress, wave

EFFORT = "ef"
RUNNER_PHASE = "runner-phase"
ITEM = {"kind": "deliver", "assignee": "", "effort": EFFORT, "executor": "inline"}


def _item(project: Project, slug: str, depends_on: list[str] | None = None) -> Record:
    return create(
        project,
        "score:work-item",
        slug,
        {"title": slug, "phase": PHASE, **ITEM, "depends_on": depends_on or []},
        "## Description\n\nd\n\n## Approach\n\na",
    )


def _acceptance(project: Project, subject: str, command: str) -> Record:
    return create(
        project,
        "score:acceptance",
        subject,
        {"method": "check", "phase": PHASE, "effort": EFFORT, "verify_command": command},
    )


def test_r14_acceptance_belongs_to_longest_subject_in_wave_end_and_task_land(
    tmp_path: Path,
) -> None:
    project, repo = _world(tmp_path, {"foo": "true", "foo-bar": "true"})
    _acceptance(project, "foo-bar-1", "false")

    owned = land_task.acceptances_for(project, "foo", PHASE)
    assert [a["subject"] for a in owned] == ["foo"]
    assert sorted(a["subject"] for a in land_task.acceptances_for(project, "foo-bar", PHASE)) == [
        "foo-bar",
        "foo-bar-1",
    ]

    _land(project, repo, "foo", "foo.txt", "foo\n")

    assert wave.end(project, repo, PHASE).merged == ("foo",)


def test_r15_gate_takes_the_latest_closing_item_as_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(project, "score:phase", PHASE, {"title": "Ph", "ordinal": 1, "effort": EFFORT})
    first = _item(project, "first")
    second = _item(project, "second", ["first"])
    project.update(first["id"], record_type="score:work-item", payload={"depends_on": ["second"]})
    project.update(second["id"], record_type="score:work-item", transition="in_progress")
    project.update(second["id"], record_type="score:work-item", transition="done")
    records = project.records()
    for record in records:
        if record["id"] == second["id"]:
            record["recorded_at"] = "2099-01-01T00:00:00Z"
    monkeypatch.setattr(Project, "records", lambda _self: records)

    terms = {term.name: term for term in gate.gate_terms(open_store(tmp_path), PHASE)}

    assert terms["verification-task-done"].holds


def test_r15_workflow_counts_an_earlier_closing_item_as_implementation(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(project, "score:phase", PHASE, {"title": "Ph", "ordinal": 1, "effort": EFFORT})
    _item(project, "base")
    middle = _item(project, "middle", ["base"])
    _item(project, "last", ["base", "middle"])
    project.update(
        middle["id"], record_type="score:work-item", payload={"depends_on": ["base", "last"]}
    )

    assert phase_progress.requires_integration_report(project.records(), PHASE)
