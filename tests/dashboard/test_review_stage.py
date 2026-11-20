from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import make_project
from conftest import git

from dashboard.backend.server import service
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record

EFFORT = "e"


def _body(phase: str) -> str:
    return (
        "## Problem\n\nP\n\n## Approach\n\nA\n\n## Exit criteria\n\nE\n\n"
        f"## Landing\n\n- Branch: `phase/{phase}`\n- Base: `main`\n"
    )


def _create(project: Project, kind: str, subject: str, payload: JsonObject, body: str) -> Record:
    return project.create(record_type=kind, subject=subject, payload=payload, body=body)


def _review_run(
    project: Project, phase: str, revision: str, *, result: str = "pass", effort: str = EFFORT
) -> None:
    _create(
        project,
        "tuner:check-run",
        f"{phase}-review",
        {
            "criterion_id": f"{phase}-review",
            "revision": revision,
            "result": result,
            "effort": effort,
            "method": "review",
            "signed_by": "",
            "evidence_kind": "review",
        },
        "Review.\n",
    )


def _project_with_phases(tmp_path: Path, *phases: str) -> tuple[Project, str]:
    project = make_project(tmp_path / "repo")
    root = project.project_root
    git(root, "config", "user.email", "test@example.com")
    git(root, "config", "user.name", "test")
    git(root, "commit", "--allow-empty", "-qm", "init")
    git(root, "branch", "-M", "main")
    git(root, "checkout", "-qb", "work")
    git(root, "commit", "--allow-empty", "-qm", "work")
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    git(root, "checkout", "-q", "main")
    for effort in (EFFORT, "other"):
        _create(project, "score:effort", effort, {"goal": "Ship", "kind": "deliver"}, "Goal.\n")
    for ordinal, phase in enumerate(phases, 1):
        git(root, "branch", f"phase/{phase}", head)
        created = _create(
            project,
            "score:phase",
            phase,
            {"title": phase, "ordinal": ordinal, "effort": EFFORT, "weight": "light"},
            _body(phase),
        )
        project.update(created["id"], transition="in_progress")
    return project, head


def _stage_ids(project: Project, phase: str) -> list[str]:
    hub = service.Reader(project).hub()
    card = next(item for item in hub.active_phases if item.subject == phase)
    assert card.progress is not None
    return [stage.id for stage in card.progress.stages]


OPEN_SPEC_STAGES = ["spec", "design", "tasks", "execute", "verify", "land", "close"]


def test_passing_review_check_run_at_phase_head_adds_no_review_cell(tmp_path: Path) -> None:
    project, head = _project_with_phases(tmp_path, "p")
    _review_run(project, "p", head)

    assert _stage_ids(project, "p") == OPEN_SPEC_STAGES


@pytest.mark.parametrize(
    ("result", "effort", "stale"),
    [("fail", EFFORT, False), ("pass", "other", False), ("pass", EFFORT, True)],
)
def test_failed_foreign_effort_or_stale_review_check_run_adds_no_review_cell(
    tmp_path: Path, result: str, effort: str, stale: bool
) -> None:
    project, head = _project_with_phases(tmp_path, "p")
    _review_run(project, "p", "deadbeefcafe" if stale else head, result=result, effort=effort)

    assert _stage_ids(project, "p") == OPEN_SPEC_STAGES


def test_review_check_run_of_another_phase_leaves_each_light_card_with_the_open_spec_stage_list(
    tmp_path: Path,
) -> None:
    project, head = _project_with_phases(tmp_path, "p", "q")
    _review_run(project, "q", head)

    assert _stage_ids(project, "p") == _stage_ids(project, "q") == OPEN_SPEC_STAGES
