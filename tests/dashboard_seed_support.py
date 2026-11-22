from __future__ import annotations

from pathlib import Path

from canon_support import make_project

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record

PHASE_BODY = (
    "## Problem\n\nP\n\n## Approach\n\nA\n\n## Exit criteria\n\nE\n\n"
    "## Requirements\n\nR1: Behavior.\n"
)


def _create(
    project: Project, kind: str, subject: str, payload: JsonObject, body: str | None = None
) -> Record:
    if body is None:
        body = "\n\n".join(f"## {name}\n\nText." for name in project.schemas().types[kind].sections)
    return project.create(record_type=kind, subject=subject, payload=payload, body=body)


def seed_project(root: Path) -> Project:
    project = make_project(root)
    _create(project, "score:effort", "e", {"goal": "Ship", "kind": "deliver"})
    phase = _create(
        project,
        "score:phase",
        "p",
        {"title": "p", "ordinal": 1, "effort": "e", "weight": "light"},
        PHASE_BODY,
    )
    project.update(phase["id"], transition="in_progress")
    task = _create(
        project,
        "score:work-item",
        "task-a",
        {"title": "a", "effort": "e", "phase": "p", "kind": "repair", "assignee": ""},
    )
    project.update(task["id"], transition="in_progress")
    _create(
        project,
        "score:acceptance",
        "task-a",
        {
            "effort": "e",
            "phase": "p",
            "method": "check",
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    _create(project, "composer:idea", "idea", {"effort": "e", "status": "open"})
    _create(
        project,
        "score:continuity-question",
        "e",
        {"owner": "user", "blocking": True, "scope": "plan"},
    )
    return project
