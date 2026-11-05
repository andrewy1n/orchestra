"""The session-start handoff hides a dormant effort through the installed hook entry point."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from conftest import REPO_ROOT, make_git_repo

PHASE_BODY = "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne"


class World:
    def __init__(self, root: Path) -> None:
        self.repo = make_git_repo()
        self.env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"ORCHESTRA_STORE", "CANON_STORE", "VIRTUAL_ENV"}
        }
        self.env["HOME"] = str(root / "home")
        (root / "home").mkdir()

    def run(
        self, tool: str, *args: str, stdin: str = "", extra_env: Mapping[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--quiet", "--project", str(REPO_ROOT), tool, *args],
            capture_output=True,
            text=True,
            cwd=str(self.repo),
            env={**self.env, **(extra_env or {})},
            input=stdin,
        )

    def create(
        self, record_type: str, subject: str, payload: Mapping[str, object], body: str
    ) -> None:
        result = self.run(
            "canon",
            "create",
            "--type",
            record_type,
            "--subject",
            subject,
            "--payload",
            json.dumps(payload),
            "--body",
            body,
        )
        assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture
def world(tmp_path: Path) -> World:
    world = World(tmp_path)
    init = world.run("canon", "init", "--schemas", "score,conductor,tuner,composer")
    assert init.returncode == 0, init.stdout + init.stderr
    for effort in ("active-one", "quiet-one"):
        world.create("score:effort", effort, {"goal": f"goal {effort}", "kind": "deliver"}, "")
        position = {"position": f"{effort} position", "scope": "effort", "effort": effort}
        world.create("score:position", effort, position, "")
    phase = {"title": "Next", "ordinal": 1, "effort": "active-one"}
    world.create("score:phase", "next-phase", phase, PHASE_BODY)
    return world


def test_session_start_handoff_lists_a_dormant_effort_on_one_line(world: World) -> None:
    later = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    result = world.run(
        "orchestra",
        "hook-start",
        "--claude",
        stdin=json.dumps({"cwd": str(world.repo)}),
        extra_env={"ORCHESTRA_NOW": later},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    context = json.loads(result.stdout.splitlines()[-1])["hookSpecificOutput"]["additionalContext"]
    assert "## active-one" in context
    assert "## quiet-one" not in context
    assert "quiet-one position" not in context
    assert "Dormant: quiet-one" in context


def test_handoff_all_shows_the_dormant_effort_in_full(world: World) -> None:
    later = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    result = world.run("orchestra", "handoff", "--all", extra_env={"ORCHESTRA_NOW": later})
    assert result.returncode == 0, result.stdout + result.stderr
    assert "quiet-one position" in result.stdout
