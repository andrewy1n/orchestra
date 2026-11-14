from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.errors import StaleWriteError
from orchestra.canon.project import Project
from orchestra.conductor import execution_cost, task_redispatch, wave

PHASE = "cost-phase"
EFFORT = "cost-effort"
LANDING = (
    "\n\n## Landing\n\nbranch: phase/cost-phase\n"
    "worktree: <repo>/.worktrees/cost-phase\nbase: main\n"
)
START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _repo(tmp_path: Path) -> tuple[Project, Path]:
    project = make_project(tmp_path)
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "base.txt").write_text("base\n")
    _git(tmp_path, "add", "base.txt")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "Cost", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Execution cost", "ordinal": 1, "effort": EFFORT},
        "## Problem\n\nProblem.\n\n## Approach\n\nApproach.\n\n"
        "## Exit criteria\n\nCriteria."
        + LANDING,
    )
    _git(tmp_path, "branch", f"phase/{PHASE}", "main")
    worktrees = tmp_path / ".worktrees"
    worktrees.mkdir()
    _git(tmp_path, "worktree", "add", "-q", str(worktrees / PHASE), f"phase/{PHASE}")
    return project, tmp_path


def _item(project: Project, slug: str, **extra: object) -> None:
    create(
        project,
        "score:work-item",
        slug,
        {
            "title": slug,
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
            **extra,
        },
        f"## Description\n\nDo {slug}.\n\n## Approach\n\nJust {slug}.",
    )


def test_wave_start_stores_dispatch_identity_with_assignment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "task")
    monkeypatch.setattr(execution_cost, "utc_now", lambda: START)

    wave.start(project, repo, PHASE)

    task = project.resolve("score:work-item", "task")
    assert task["lifecycle_state"] == "in_progress"
    assert task["payload"]["assignee"] == "inline"
    assert task["payload"]["write_root"] == str(repo / ".worktrees" / f"{PHASE}--task")
    assert task["payload"].get("dispatch_id")
    assert task["payload"].get("dispatched_at") == START.isoformat(timespec="microseconds")


def test_redispatch_replaces_markers_and_increments_attempts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "task")
    clock = [START]
    monkeypatch.setattr(execution_cost, "utc_now", lambda: clock[0])
    wave.start(project, repo, PHASE)
    first = project.resolve("score:work-item", "task")
    first_dispatch = first["payload"]["dispatch_id"]
    clock[0] += timedelta(seconds=90)

    retried = task_redispatch.redispatch(
        project, "task", expected_revision=first["revision"]
    )

    assert retried["lifecycle_state"] == "in_progress"
    assert retried["payload"].get("attempts") == 1
    assert retried["payload"].get("dispatch_id") != first_dispatch
    assert retried["payload"].get("dispatched_at") == clock[0].isoformat(timespec="microseconds")
    assert retried["payload"]["assignee"] == first["payload"]["assignee"]
    assert retried["payload"]["write_root"] == first["payload"]["write_root"]


def test_redispatch_rejects_stale_revision_without_writing(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "task")
    wave.start(project, repo, PHASE)
    first = project.resolve("score:work-item", "task")
    project.update(
        first["id"], record_type="score:work-item", payload={"attempts": 0}
    )
    current = project.resolve("score:work-item", "task")

    with pytest.raises(StaleWriteError):
        task_redispatch.redispatch(project, "task", expected_revision=first["revision"])

    assert project.get(current["id"])["payload"] == current["payload"]


@pytest.mark.parametrize("state", ["planned", "done"])
def test_redispatch_rejects_tasks_outside_in_progress(
    tmp_path: Path, state: str
) -> None:
    project, _ = _repo(tmp_path)
    _item(project, "task")
    task = project.resolve("score:work-item", "task")
    if state == "done":
        project.update(task["id"], record_type="score:work-item", transition="in_progress")
        task = project.resolve("score:work-item", "task")
        project.update(task["id"], record_type="score:work-item", transition="done")
        task = project.resolve("score:work-item", "task")

    with pytest.raises(task_redispatch.RedispatchError, match="in_progress"):
        task_redispatch.redispatch(project, "task", expected_revision=task["revision"])


def test_legacy_in_progress_task_without_dispatch_fields_can_be_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, _ = _repo(tmp_path)
    _item(project, "task", attempts=0)
    task = project.resolve("score:work-item", "task")
    project.update(
        task["id"],
        record_type="score:work-item",
        transition="in_progress",
        payload={"assignee": "inline", "write_root": str(tmp_path)},
    )
    task = project.resolve("score:work-item", "task")
    monkeypatch.setattr(execution_cost, "utc_now", lambda: START)

    retried = task_redispatch.redispatch(
        project, "task", expected_revision=task["revision"]
    )

    assert retried["payload"].get("attempts") == 1
    assert retried["payload"].get("dispatch_id")
    assert retried["payload"].get("dispatched_at") == START.isoformat(timespec="microseconds")
