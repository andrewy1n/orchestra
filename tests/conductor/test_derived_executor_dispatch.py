from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.project import Project
from orchestra.conductor.tasks.wave import WaveError, start

PHASE = "derived-executor"
EFFORT = "executor-test"
PHASE_BODY = (
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
        '[verify.unit]\nrunner = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]\n'
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
        PHASE_BODY,
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
    size: str,
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
        "size": size,
    }
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


def test_r9_wave_start_uses_configured_budget_without_persisting_prediction(
    tmp_path: Path,
) -> None:
    project, repo = _repo(tmp_path, budget=16)
    _item(project, "first", size="XS", estimate_minutes=8)
    _item(project, "second", size="XS", estimate_minutes=8)

    result = start(project, repo, PHASE)

    assert {task.executor for task in result.tasks} == {"inline"}
    for subject in ("first", "second"):
        payload = project.resolve("score:work-item", subject)["payload"]
        assert payload["assignee"] == "inline"
        assert "executor" not in payload


def test_r10_wave_start_preserves_an_explicit_executor_override(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "small", size="XS", executor="subagent")

    result = start(project, repo, PHASE)

    assert [task.executor for task in result.tasks] == ["subagent"]


def test_r11_bad_execute_config_fails_before_task_dispatch(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "small", size="XS")
    config_path = repo / "orchestra.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "small_wave_budget_minutes = 15", "small_wave_budget_minutes = -1"
        ),
        encoding="utf-8",
    )

    with pytest.raises(WaveError, match="small_wave_budget_minutes"):
        start(project, repo, PHASE)

    assert project.resolve("score:work-item", "small")["lifecycle_state"] == "planned"
    assert not (repo / ".worktrees" / f"{PHASE}--small").exists()


def test_r13_wave_start_keeps_the_first_dispatch_executor(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "retry", size="XS", assignee="subagent")

    result = start(project, repo, PHASE)

    assert [task.executor for task in result.tasks] == ["subagent"]
