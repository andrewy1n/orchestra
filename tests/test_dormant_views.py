from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from canon_support import REPO, create, make_project

from dashboard.backend.snapshot import load_snapshot
from orchestra.canon.project import Project

PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne"


def _world(tmp_path: Path) -> tuple[Project, datetime]:
    project = make_project(tmp_path)
    for effort in ("busy", "quiet"):
        create(project, "score:effort", effort, {"goal": f"goal of {effort}", "kind": "deliver"})
        position = {"position": f"{effort} position", "scope": "effort", "effort": effort}
        create(project, "score:position", effort, position)
    create(
        project,
        "score:phase",
        "next-up",
        {"title": "Next up", "ordinal": 1, "effort": "busy"},
        PHASE_BODY,
    )
    return project, datetime.now(timezone.utc) + timedelta(days=10)


def _run(
    repo: Path, now: datetime, *args: str, stdin: str = ""
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO), ORCHESTRA_NOW=now.isoformat())
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *args],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
        input=stdin,
    )


def test_r10_the_session_start_handoff_leaves_a_dormant_effort_out(tmp_path: Path) -> None:
    _, later = _world(tmp_path)
    result = _run(
        tmp_path, later, "hook-start", "--claude", stdin=json.dumps({"cwd": str(tmp_path)})
    )
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout.splitlines()[-1])["hookSpecificOutput"]["additionalContext"]
    assert "## busy" in context
    assert "## quiet" not in context
    assert "quiet position" not in context
    assert "Dormant: quiet" in context


def test_r11_handoff_all_shows_a_dormant_effort_in_full(tmp_path: Path) -> None:
    _, later = _world(tmp_path)
    default = _run(tmp_path, later, "handoff")
    assert "## quiet" not in default.stdout
    assert "Dormant: quiet" in default.stdout
    everything = _run(tmp_path, later, "handoff", "--all")
    assert "## quiet" in everything.stdout
    assert "quiet position" in everything.stdout
    assert "Dormant:" not in everything.stdout


def test_r11_handoff_for_one_effort_shows_it_even_when_dormant(tmp_path: Path) -> None:
    _, later = _world(tmp_path)
    result = _run(tmp_path, later, "handoff", "--effort", "quiet")
    assert "quiet position" in result.stdout


def test_r12_the_dashboard_snapshot_marks_a_dormant_effort(tmp_path: Path) -> None:
    project, later = _world(tmp_path)
    snapshot = load_snapshot(project, now=later)
    marks = {view.effort: view.dormant for view in snapshot.efforts}
    assert marks == {"busy": False, "quiet": True}
    assert project.resolve("score:effort", "quiet")["payload"].get("status") is None
