from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from canon_support import REPO, create, make_project

from orchestra.canon.project import Project

PHASE = "derived-executor"
EFFORT = "executor-test"
LANDING = (
    "## Problem\n\nA test phase.\n\n## Approach\n\nTest dispatch.\n\n"
    "## Exit criteria\n\nWave dispatch passes.\n\n"
    "## Landing\n\nbranch: phase/derived-executor\n"
    "base: main\n"
)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _repo(tmp_path: Path, *, budget: int = 15) -> tuple[Project, Path]:
    project = make_project(tmp_path)
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "test")
    (tmp_path / "base.txt").write_text("base\n", encoding="utf-8")
    (tmp_path / "orchestra.toml").write_text(
        '[verify.stages]\ntask = ["unit"]\nphase = ["unit", "review"]\n\n'
        ' [verify.unit]\nrunner = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]\n'
        f"\n[execute]\nsmall_wave_budget_minutes = {budget}\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", "base.txt", "orchestra.toml")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "test", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Derived executor test", "ordinal": 1, "effort": EFFORT},
        LANDING,
    )
    _git(tmp_path, "branch", f"phase/{PHASE}", "main")
    (tmp_path / ".worktrees").mkdir(exist_ok=True)
    _git(
        tmp_path,
        "worktree",
        "add",
        "-q",
        str(tmp_path / ".worktrees" / PHASE),
        f"phase/{PHASE}",
    )
    return project, tmp_path


def _item(
    project: Project,
    slug: str,
    *,
    size: str | None = None,
    estimate_minutes: int | None = None,
    executor: str | None = None,
    assignee: str = "",
) -> None:
    payload: dict[str, object] = {
        "title": slug,
        "phase": PHASE,
        "kind": "deliver",
        "assignee": assignee,
        "effort": EFFORT,
    }
    if size is not None:
        payload["size"] = size
    if estimate_minutes is not None:
        payload["estimate_minutes"] = estimate_minutes
    if executor is not None:
        payload["executor"] = executor
    create(
        project,
        "score:work-item",
        slug,
        payload,
        f"## Description\n\nDo {slug}.\n\n## Approach\n\nTest {slug}.",
    )


def _start(repo: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "wave", "start", PHASE, "--json"],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )


@pytest.mark.parametrize(("budget", "expected"), [(15, "subagent"), (16, "inline")])
def test_r9_cli_uses_configured_small_wave_budget(
    tmp_path: Path, budget: int, expected: str
) -> None:
    project, repo = _repo(tmp_path, budget=budget)
    _item(project, "first", size="XS", estimate_minutes=8)
    _item(project, "second", size="XS", estimate_minutes=8)

    result = _start(repo)

    assert result.returncode == 0, result.stderr
    assert {task["executor"] for task in json.loads(result.stdout)["tasks"]} == {expected}
    assert all(
        "executor" not in project.resolve("score:work-item", task)["payload"]
        for task in ("first", "second")
    )


def test_r11_cli_reports_conflicting_written_executors_before_dispatch(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "first", size="XS", executor="inline")
    _item(project, "second", size="XS", executor="subagent")

    result = _start(repo)

    assert result.returncode == 2
    assert "first=inline" in result.stderr
    assert "second=subagent" in result.stderr
    assert not (repo / ".worktrees" / f"{PHASE}--first").exists()


def test_r13_cli_redispatch_keeps_the_first_executor(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "retry", size="XS", assignee="subagent")

    result = _start(repo)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["tasks"][0]["executor"] == "subagent"
