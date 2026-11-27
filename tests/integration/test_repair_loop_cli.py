from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from canon_support import create, make_project
from conductor_support import PHASE as GATE_PHASE
from conductor_support import Cli, seed
from conftest import REPO_ROOT, git

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject
from orchestra.cli import main as cli_main

PHASE = "repair-phase"
EFFORT = "repair-effort"
TASK = "repair-task"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _world(root: Path) -> tuple[Project, Path]:
    project = make_project(root)
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    (root / "base.txt").write_text("base\n")
    _git(root, "add", "base.txt")
    _git(root, "commit", "-qm", "base")
    _git(root, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "Repair", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Repair loop", "ordinal": 1, "effort": EFFORT},
        "## Problem\n\nProblem.\n\n## Approach\n\nApproach.\n\n"
        "## Exit criteria\n\nCriteria.\n\n## Landing\n\n"
        f"branch: phase/{PHASE}\nbase: main\n",
    )
    _git(root, "branch", f"phase/{PHASE}", "main")
    (root / ".worktrees").mkdir()
    _git(root, "worktree", "add", "-q", str(root / ".worktrees" / PHASE), f"phase/{PHASE}")
    create(
        project,
        "score:work-item",
        TASK,
        {
            "title": "Repair task",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
            "requirements": ["R1"],
        },
        "## Description\n\nRepair.\n\n## Approach\n\nDo it.",
    )
    create(
        project,
        "score:acceptance",
        TASK,
        {
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "false",
            "requirement": "R1",
        },
    )
    return project, root


def _invoke(
    root: Path, args: list[str], capsys: pytest.CaptureFixture[str]
) -> tuple[int, str, str]:
    argv = [*args, "--cwd", str(root), "--store", str(root)]
    try:
        code = cli_main(argv)
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 1
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _redispatch(
    project: Project, root: Path, capsys: pytest.CaptureFixture[str]
) -> tuple[int, dict[str, object]]:
    revision = project.resolve("score:work-item", TASK)["revision"]
    code, out, err = _invoke(
        root, ["task", "redispatch", TASK, "--expected-revision", revision, "--json"], capsys
    )
    assert code == 0, err
    return code, json.loads(out)


def _payload(project: Project) -> JsonObject:
    return project.resolve("score:work-item", TASK)["payload"]


def _counts(project: Project) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in project.list("conductor:redispatch-attempt"):
        key = str(event["payload"]["failure_key"])
        counts[key] = counts.get(key, 0) + 1
    return counts


def test_rerun_consumes_no_repair_attempt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project, root = _world(tmp_path)
    code, _, err = _invoke(root, ["wave", "start", PHASE], capsys)
    assert code == 0, err
    acceptance = project.resolve("score:acceptance", TASK)["id"]

    code, _, err = _invoke(root, ["check", "--acceptance", acceptance, "--allow-dirty"], capsys)
    assert code != 0, err
    assert _payload(project).get("attempts", 0) == 0
    assert _counts(project) == {}

    _, first = _redispatch(project, root, capsys)
    key = first["failure_key"]
    assert first["attempts"] == 1
    assert key
    assert _counts(project) == {key: 1}

    _invoke(root, ["check", "--acceptance", acceptance, "--allow-dirty"], capsys)
    payload = _payload(project)
    assert payload["attempts"] == 1
    assert _counts(project) == {key: 1}

    _, second = _redispatch(project, root, capsys)
    assert second["failure_key"] == key
    assert second["attempts"] == 2
    assert _counts(project) == {key: 2}

    before = _payload(project)
    events_before = _counts(project)
    code, out, err = _invoke(root, ["task", "resume", TASK, "--json"], capsys)
    if shutil.which("lsof") is None:
        pytest.skip("lsof is not installed")
    assert code == 0, err
    assert json.loads(out)["task"] == TASK
    after = _payload(project)
    assert after["attempts"] == before["attempts"]
    assert _counts(project) == events_before


def _orchestra(store: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in {"ORCHESTRA_STORE", "CANON_STORE"}}
    env["PYTHONPATH"] = os.pathsep.join(
        dict.fromkeys([str(REPO_ROOT), *filter(None, [env.get("PYTHONPATH")])])
    )
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *args, "--store", str(store)],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
    )


def test_repeat_review_verdict_binds_to_landing_revision(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, review=False, runner_check=False)
    worktree = phase.repo / ".worktrees" / GATE_PHASE
    git(phase.repo, "worktree", "add", "-q", str(worktree), "phase/x")
    reviewed = git(worktree, "rev-parse", "HEAD").stdout.strip()
    phase.review("fail", revision=reviewed)

    (worktree / "repair.txt").write_text("repair\n")
    git(worktree, "add", "repair.txt")
    git(worktree, "commit", "-qm", "repair")
    head = git(worktree, "rev-parse", "HEAD").stdout.strip()
    assert head != reviewed
    phase.check_run(revision=head)

    brief = _orchestra(
        store,
        "review-brief",
        "--cwd",
        str(worktree),
        "--base",
        "main",
        "--phase-head",
        "HEAD",
        "--phase",
        GATE_PHASE,
        cwd=store,
    )
    assert brief.returncode == 0, brief.stdout + brief.stderr
    assert "## Prior review" in brief.stdout
    assert reviewed in brief.stdout
    assert "## Repair diff" in brief.stdout
    assert "+repair" in brief.stdout
    assert "## Affected callers" in brief.stdout

    assert "review-at-head" in phase.missing()
    assert _orchestra(store, "gate", GATE_PHASE, cwd=store).returncode == 1

    phase.review("pass", revision=head)
    assert "review-at-head" not in phase.missing()
    assert phase.term("review-at-head").holds
    assert _orchestra(store, "gate", GATE_PHASE, cwd=store).returncode == 0

    (worktree / "later.py").write_text("X = 1\n")
    git(worktree, "add", "later.py")
    git(worktree, "commit", "-qm", "later")
    assert not phase.term("head-descends-from-review").holds
    assert _orchestra(store, "gate", GATE_PHASE, cwd=store).returncode == 1
