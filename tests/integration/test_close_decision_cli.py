from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from canon_support import REPO, create, make_project

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject
from orchestra.conductor import wave

PHASE = "ph"
EFFORT = "ef"
PHASE_BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n"
    "## Landing\n\nbranch: phase/ph\nworktree: <repo>/.worktrees/ph\nbase: main\n"
)
SPEC_BODY = (
    "## Requirements\n\nR1: It works.\n\n## Acceptance criteria\n\nx\n\n## Constraints\n\nx\n\n"
    "## Non-goals\n\nx\n\n## Invariants\n\nx\n\n## Assumptions\n\nx"
)
EVIDENCE = {
    "subject": "a",
    "kind": "deliver",
    "result": "pass",
    "verdict": "pass",
    "evidence": "ran the acceptance",
}


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True)


def _world(tmp_path: Path, method: str) -> Project:
    project = make_project(tmp_path)
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "base.txt").write_text("base\n")
    _git(tmp_path, "add", "base.txt")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(
        project, "score:phase", PHASE, {"title": "Ph", "ordinal": 1, "effort": EFFORT}, PHASE_BODY
    )
    create(
        project,
        "score:specification",
        PHASE,
        {"weight": "full", "phase": PHASE, "effort": EFFORT, "requirements": ["R1"]},
        SPEC_BODY,
    )
    _git(tmp_path, "branch", f"phase/{PHASE}", "main")
    (tmp_path / ".worktrees").mkdir()
    _git(tmp_path, "worktree", "add", "-q", str(tmp_path / ".worktrees" / PHASE), f"phase/{PHASE}")
    create(
        project,
        "score:work-item",
        "a",
        {
            "title": "a",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
            "requirements": ["R1"],
        },
        "## Description\n\nR1: It works.\n\n## Approach\n\nDo it.",
    )
    create(
        project,
        "score:acceptance",
        "a",
        {
            "method": method,
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    wave.start(project, tmp_path, PHASE)
    return project


def _orchestra(cwd: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *argv],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def _task_land(project: Project, repo: Path) -> JsonObject:
    evidence = repo / "evidence.json"
    evidence.write_text(json.dumps(EVIDENCE))
    result = _orchestra(repo, "task", "land", "a", "--evidence", str(evidence), "--json")
    assert result.returncode in (0, 1), result.stderr
    landed: JsonObject = json.loads(result.stdout)
    return landed


def _close_batch(project: Project, repo: Path, elsewhere: Path) -> subprocess.CompletedProcess[str]:
    item = project.resolve("score:work-item", "a")
    acceptance = project.resolve("score:acceptance", "a")
    green = max(
        (
            r
            for r in project.list("tuner:check-run")
            if r["payload"].get("criterion_id") == acceptance["id"]
        ),
        key=lambda r: r["recorded_at"],
    )
    request: JsonObject = {
        "subject": "a",
        "effort": EFFORT,
        "work_item_id": item["id"],
        "transition": "done",
        "acceptance_ids": [acceptance["id"]],
        "criteria": [
            {
                "criterion_id": acceptance["id"],
                "method": acceptance["payload"]["method"],
                "result": green["payload"]["result"],
                "check_run_id": green["id"],
            }
        ],
    }
    path = elsewhere / "request.json"
    path.write_text(json.dumps(request))
    return _orchestra(elsewhere, "close-batch", "--input", str(path), "--store", str(repo))


def test_task_land_and_close_batch_approve_the_same_records(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    project = _world(repo, "check")

    landed = _task_land(project, repo)
    batch = _close_batch(project, repo, elsewhere)

    assert landed["state"] == "done"
    assert batch.returncode == 0, batch.stderr
    operations = [json.loads(line) for line in batch.stdout.splitlines()]
    assert [op["op"] for op in operations] == ["update"]


def test_task_land_and_close_batch_refuse_with_the_same_reason(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    project = _world(repo, "tdd")

    landed = _task_land(project, repo)
    batch = _close_batch(project, repo, elsewhere)

    reasons = landed["reasons"]
    assert isinstance(reasons, list)
    assert landed["state"] == "in_progress"
    assert batch.returncode == 2
    assert batch.stdout == ""
    assert len(reasons) == 1
    assert isinstance(reasons[0], str)
    assert batch.stderr.strip() == f"close refused: {reasons[0]}"
