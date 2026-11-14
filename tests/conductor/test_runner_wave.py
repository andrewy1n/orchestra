from __future__ import annotations

from pathlib import Path

from canon_support import create, make_project

from orchestra.canon.project import Project
from orchestra.conductor import wave
from orchestra.tools import Git

PHASE = "runner-phase"
EFFORT = "runner-effort"
PHASE_BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n"
    f"## Landing\n\nbranch: phase/{PHASE}\nworktree: <repo>/.worktrees/{PHASE}\nbase: main\n"
)


def _world(tmp_path: Path) -> tuple[Project, Path]:
    project = make_project(tmp_path)
    git = Git(tmp_path)
    git.run("config", "user.email", "test@example.com")
    git.run("config", "user.name", "test")
    (tmp_path / "base.txt").write_text("base\n")
    git.run("add", "base.txt")
    git.run("commit", "-qm", "base")
    git.run("branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": PHASE, "ordinal": 1, "effort": EFFORT},
        PHASE_BODY,
    )
    git.run("branch", f"phase/{PHASE}", "main")
    (tmp_path / ".worktrees").mkdir()
    git.run("worktree", "add", "-q", str(tmp_path / ".worktrees" / PHASE), f"phase/{PHASE}")
    return project, tmp_path


def _item(
    project: Project,
    slug: str,
    *,
    executor: str = "inline",
    depends_on: list[str] | None = None,
) -> None:
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
            "executor": executor,
            "depends_on": depends_on or [],
        },
        f"## Description\n\nDo {slug}.\n\n## Approach\n\nImplement {slug}.",
    )


def test_r11_ordinary_wave_reports_agent_execution(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    _item(project, "first", executor="subagent")
    _item(project, "second", executor="subagent")

    started = wave.start(project, repo, PHASE)

    assert getattr(started, "execution_mode", "") == "agent"
    assert [item.executor for item in started.tasks] == ["subagent", "subagent"]


def test_r2_phase_closing_task_depends_on_every_live_item(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    _item(project, "first")
    _item(project, "second")
    _item(project, "closing", depends_on=["first"])
    records = project.records()
    closing = next(record for record in records if record["subject"] == "closing")

    assert not wave.closes_phase(closing, wave.phase_items(records, PHASE))
