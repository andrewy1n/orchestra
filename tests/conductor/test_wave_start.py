from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from canon_support import REPO, create, make_project

from orchestra.canon.project import Project
from orchestra.conductor import wave

PHASE = "ph"
EFFORT = "ef"
LANDING = "\n\n## Landing\n\nbranch: phase/ph\nworktree: <repo>/.worktrees/ph\nbase: main\n"
PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _repo(tmp_path: Path, landing: bool = True) -> tuple[Project, Path]:
    project = make_project(tmp_path)
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "base.txt").write_text("base\n")
    _git(tmp_path, "add", "base.txt")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Ph", "ordinal": 1, "effort": EFFORT},
        PHASE_BODY + (LANDING if landing else ""),
    )
    _git(tmp_path, "branch", f"phase/{PHASE}", "main")
    (tmp_path / ".worktrees").mkdir(exist_ok=True)
    _git(tmp_path, "worktree", "add", "-q", str(tmp_path / ".worktrees" / PHASE), f"phase/{PHASE}")
    return project, tmp_path


def _item(project: Project, slug: str, executor: str = "inline", **extra: object) -> None:
    payload = {
        "title": slug,
        "phase": PHASE,
        "kind": "deliver",
        "assignee": "",
        "effort": EFFORT,
        "executor": executor,
        **extra,
    }
    create(
        project,
        "score:work-item",
        slug,
        payload,  # pyright: ignore[reportArgumentType]  # The test payload holds JSON values only.
        f"## Description\n\nDo {slug}.\n\n## Approach\n\nJust {slug}.",
    )


def test_r01_lists_the_ready_items_of_the_lowest_wave(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "a")
    _item(project, "b")
    _item(project, "c", depends_on=["a"])
    started = wave.start(project, repo, PHASE)
    assert [t.task for t in started.tasks] == ["a", "b"]


def test_r02_refuses_a_wave_whose_tasks_disagree_on_executor(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "a", executor="inline")
    _item(project, "b", executor="subagent")
    with pytest.raises(wave.WaveError, match=r"a=inline.*b=subagent"):
        wave.start(project, repo, PHASE)
    assert not (repo / ".worktrees" / "ph--a").exists()


def test_r03_creates_each_task_branch_and_worktree_from_the_phase_tip(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "a")
    _item(project, "b")
    tip = _git(repo, "rev-parse", "phase/ph")
    wave.start(project, repo, PHASE)
    for slug in ("a", "b"):
        assert _git(repo, "rev-parse", f"task/ph/{slug}") == tip
        assert (repo / ".worktrees" / f"ph--{slug}").is_dir()


def test_r03_the_closing_task_runs_in_the_phase_worktree(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "a")
    wave.start(project, repo, PHASE)
    task = project.resolve("score:work-item", "a")
    project.update(task["id"], record_type="score:work-item", transition="done")
    _item(project, "verify-ph", depends_on=["a"])
    started = wave.start(project, repo, PHASE)
    assert [t.write_root for t in started.tasks] == [str(repo / ".worktrees" / PHASE)]
    assert started.tasks[0].branch == "phase/ph"


def test_r04_reuses_a_task_branch_and_merges_the_phase_tip_into_it(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "a")
    _git(repo, "branch", "task/ph/a", "phase/ph")
    _git(repo, "worktree", "add", "-q", str(repo / ".worktrees" / "ph--a"), "task/ph/a")
    phase_tree = repo / ".worktrees" / PHASE
    (phase_tree / "later.txt").write_text("later\n")
    _git(phase_tree, "add", "later.txt")
    _git(phase_tree, "commit", "-qm", "later")
    wave.start(project, repo, PHASE)
    assert (repo / ".worktrees" / "ph--a" / "later.txt").read_text() == "later\n"


def test_r05_moves_each_task_to_in_progress_with_assignee_and_write_root(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "a", executor="subagent")
    wave.start(project, repo, PHASE)
    record = project.resolve("score:work-item", "a")
    assert record["lifecycle_state"] == "in_progress"
    payload = record["payload"]
    assert payload["assignee"] == "subagent"
    assert payload["write_root"] == str(repo / ".worktrees" / "ph--a")


def test_r05_without_landing_the_write_root_is_the_checkout(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path, landing=False)
    _item(project, "a")
    started = wave.start(project, repo, PHASE)
    assert started.tasks[0].write_root == str(repo)
    assert not (repo / ".worktrees" / "ph--a").exists()


def test_r06_the_cli_prints_each_task_brief(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "a")
    env = dict(os.environ, PYTHONPATH=str(REPO))
    result = subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "wave", "start", PHASE, "--json"],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    task = json.loads(result.stdout)["tasks"][0]
    assert task["task"] == "a"
    assert "Just a." in task["brief"]
