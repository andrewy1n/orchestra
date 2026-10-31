"""Temp canon stores for the view and hook tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = os.pathsep.join(
    [
        str(REPO / "orchestra" / "score" / "schemas" / "score.json"),
        str(REPO / "orchestra" / "conductor" / "schemas" / "conductor.json"),
        str(REPO / "orchestra" / "tuner" / "schemas" / "tuner.json"),
        str(REPO / "orchestra" / "composer" / "schemas" / "composer.json"),
    ]
)

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
os.environ["CANON_SCHEMA_PATH"] = SCHEMA_PATH

from orchestra.canon.project import Project, open_store  # noqa: E402


def make_project(root: Path) -> Project:
    root.mkdir(parents=True, exist_ok=True)
    git_init = subprocess.run(
        ["git", "-C", str(root), "init", "-q"], capture_output=True, text=True
    )
    if git_init.returncode:
        raise RuntimeError(git_init.stdout + git_init.stderr)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "orchestra.canon",
            "--root",
            str(root),
            "init",
            "--schemas",
            "score,conductor,tuner,composer",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return open_store(root)


def create(project, record_type: str, subject: str, payload: dict, body: str | None = None):
    if body is None:
        sections = project.schemas().types[record_type].sections
        body = "\n\n".join(f"## {name}\n\nText." for name in sections)
    return project.create(
        record_type=record_type, subject=subject, payload=payload, body=body
    )


def seed_effort(project, effort: str = "alpha", phase: str = "p1") -> None:
    create(project, "score:effort", effort, {"goal": f"Goal of {effort}", "kind": "deliver"})
    create(
        project,
        "score:position",
        effort,
        {"position": "midway", "scope": "effort", "effort": effort},
    )
    create(
        project,
        "score:phase",
        phase,
        {"title": "Phase one", "ordinal": 1, "effort": effort},
    )
