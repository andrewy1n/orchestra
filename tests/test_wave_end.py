from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from canon_support import REPO, create, make_project

from orchestra.canon.project import Project
from orchestra.conductor import land_task, wave

PHASE = "ph"
EFFORT = "ef"
PHASE_BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n"
    "## Landing\n\nbranch: phase/ph\nworktree: <repo>/.worktrees/ph\nbase: main\n"
)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _world(tmp_path: Path, commands: dict[str, str]) -> tuple[Project, Path]:
    project = make_project(tmp_path)
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "shared.txt").write_text("base\n")
    _git(tmp_path, "add", "shared.txt")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(
        project, "score:phase", PHASE, {"title": "Ph", "ordinal": 1, "effort": EFFORT}, PHASE_BODY
    )
    _git(tmp_path, "branch", f"phase/{PHASE}", "main")
    (tmp_path / ".worktrees").mkdir()
    _git(tmp_path, "worktree", "add", "-q", str(tmp_path / ".worktrees" / PHASE), f"phase/{PHASE}")
    for slug, command in commands.items():
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
            },
            "## Description\n\nd\n\n## Approach\n\na",
        )
        create(
            project,
            "score:acceptance",
            slug,
            {"method": "check", "phase": PHASE, "effort": EFFORT, "verify_command": command},
        )
    wave.start(project, tmp_path, PHASE)
    return project, tmp_path


def _land(project: Project, repo: Path, slug: str, file: str, text: str) -> None:
    (repo / ".worktrees" / f"{PHASE}--{slug}" / file).write_text(text)
    evidence = repo / f"{slug}.json"
    evidence.write_text(
        json.dumps(
            {
                "subject": slug,
                "kind": "deliver",
                "result": "pass",
                "verdict": "pass",
                "evidence": "e",
            }
        )
    )
    land_task.land(project, repo, slug, evidence)


def test_r12_merges_passing_task_branches_in_task_slug_order(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"b": "true", "a": "true"})
    _land(project, repo, "b", "b.txt", "b\n")
    _land(project, repo, "a", "a.txt", "a\n")
    result = wave.end(project, repo, PHASE)
    assert result.merged == ("a", "b")
    tree = repo / ".worktrees" / PHASE
    assert (tree / "a.txt").exists() and (tree / "b.txt").exists()
    log = _git(tree, "log", "--first-parent", "--format=%s").splitlines()
    assert any("task/ph/b" in line for line in log) or "b.txt" in _git(
        tree, "show", "--name-only", "--format=", "HEAD"
    )
    first_a = _git(tree, "log", "--format=%H", "--diff-filter=A", "--", "a.txt").splitlines()[-1]
    first_b = _git(tree, "log", "--format=%H", "--diff-filter=A", "--", "b.txt").splitlines()[-1]
    order = _git(tree, "rev-list", "--topo-order", "--reverse", "HEAD").splitlines()
    assert order.index(first_a) < order.index(first_b)


def test_r13_stops_at_a_conflict_and_opens_a_blocking_question(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"a": "true", "b": "true", "c": "true"})
    _land(project, repo, "a", "shared.txt", "from a\n")
    _land(project, repo, "b", "shared.txt", "from b\n")
    _land(project, repo, "c", "c.txt", "c\n")
    result = wave.end(project, repo, PHASE)
    assert result.merged == ("a",)
    assert result.conflict == "b"
    tree = repo / ".worktrees" / PHASE
    assert "<<<<<<<" in (tree / "shared.txt").read_text()
    assert (Path(_git(tree, "rev-parse", "--git-dir")) / "MERGE_HEAD").exists() or _git(
        tree, "ls-files", "--unmerged"
    )
    question = project.get(result.question_id, "score:continuity-question")
    assert question["payload"]["scope"] == "merge:b"
    assert question["payload"]["blocking"] is True
    assert not (tree / "c.txt").exists()


def test_r13_the_cli_exits_non_zero_on_a_conflict(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"a": "true", "b": "true"})
    _land(project, repo, "a", "shared.txt", "from a\n")
    _land(project, repo, "b", "shared.txt", "from b\n")
    env = dict(os.environ, PYTHONPATH=str(REPO))
    result = subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "wave", "end", PHASE, "--json"],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["conflict"] == "b"


def test_r14_never_merges_a_task_branch_whose_checks_did_not_pass(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"a": "true", "b": "false"})
    _land(project, repo, "a", "a.txt", "a\n")
    _land(project, repo, "b", "b.txt", "b\n")
    result = wave.end(project, repo, PHASE)
    assert result.merged == ("a",)
    assert result.skipped == (("b", "checks did not pass"),)
    assert not (repo / ".worktrees" / PHASE / "b.txt").exists()
