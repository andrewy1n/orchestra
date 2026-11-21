from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from canon_support import REPO, create, make_project

from orchestra.canon.project import Project

PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne"


def _effort(project: Project, name: str) -> None:
    create(project, "score:effort", name, {"goal": f"goal of {name}", "kind": "deliver"})
    position = {"position": f"{name} position", "scope": "effort", "effort": name}
    create(project, "score:position", name, position)


def _phase(project: Project, name: str, effort: str) -> str:
    record = create(
        project,
        "score:phase",
        name,
        {"title": name, "ordinal": 1, "effort": effort},
        PHASE_BODY,
    )
    return record["id"]


def _world(tmp_path: Path) -> datetime:
    project = make_project(tmp_path)
    for name in ("busy", "quiet", "retired", "complete"):
        _effort(project, name)
    _phase(project, "busy-phase", "busy")
    done = _phase(project, "complete-phase", "complete")
    project.update(done, transition="in_progress")
    project.update(done, transition="done")
    goal = project.resolve("score:effort", "retired")
    project.supersede(goal["id"], payload={**goal["payload"], "status": "closed"})
    return datetime.now(timezone.utc) + timedelta(days=10)


def _handoff(repo: Path, now: datetime) -> str:
    env = dict(os.environ, PYTHONPATH=str(REPO), ORCHESTRA_NOW=now.isoformat())
    result = subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "handoff"],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_handoff_lists_every_effort_with_its_status_label(tmp_path: Path) -> None:
    text = _handoff(tmp_path, _world(tmp_path))
    labels = dict(re.findall(r"^## (\S+) \((closed|finished|dormant|live)\)$", text, re.M))
    assert labels == {
        "busy": "live",
        "quiet": "dormant",
        "retired": "closed",
        "complete": "finished",
    }
