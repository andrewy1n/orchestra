"""A light phase analyzes through the installed entry points with no specification or design."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from conftest import REPO_ROOT, make_git_repo

PHASE = "light-e2e"
EFFORT = "light-effort"
PHASE_BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n"
    "## Requirements\n\nR1: First behavior.\nR2: Second behavior.\n"
)


class World:
    def __init__(self, root: Path) -> None:
        self.store = make_git_repo()
        self.env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"ORCHESTRA_STORE", "CANON_STORE", "VIRTUAL_ENV"}
        }
        self.env["HOME"] = str(root / "home")
        (root / "home").mkdir()

    def run(self, tool: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--quiet", "--project", str(REPO_ROOT), tool, *args],
            capture_output=True,
            text=True,
            cwd=str(self.store),
            env=self.env,
        )

    def create(self, record_type: str, subject: str, payload: dict[str, object], body: str) -> None:
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

    def records(self, record_type: str) -> int:
        result = self.run(
            "canon", "list", "--type", record_type, "--format", "tsv", "--fields", "id"
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return max(len(result.stdout.splitlines()) - 1, 0)


@pytest.fixture
def world(tmp_path: Path) -> World:
    world = World(tmp_path)
    init = world.run("canon", "init", "--schemas", "score,conductor,tuner,composer")
    assert init.returncode == 0, init.stdout + init.stderr
    return world


def _seed_light_phase(world: World) -> None:
    world.create("score:effort", EFFORT, {"goal": "g", "kind": "deliver"}, "")
    world.create(
        "score:phase",
        PHASE,
        {"title": PHASE, "ordinal": 1, "effort": EFFORT, "weight": "light"},
        PHASE_BODY,
    )
    world.create(
        "score:work-item",
        "light-impl",
        {
            "title": "Implement",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "requirements": ["R1", "R2"],
        },
        "## Description\n\nR1: First behavior.\nR2: Second behavior.",
    )
    world.create(
        "score:acceptance",
        "light-impl",
        {
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirements": ["R1", "R2"],
        },
        "",
    )


def test_light_phase_analyzes_clean_with_no_specification_or_design(world: World) -> None:
    _seed_light_phase(world)
    result = world.run("orchestra", "analyze", PHASE)
    assert result.returncode == 0, result.stdout + result.stderr
    assert world.records("score:specification") == 0
    assert world.records("score:design") == 0


def test_light_phase_analysis_reports_a_requirement_no_acceptance_names(world: World) -> None:
    _seed_light_phase(world)
    world.create(
        "score:work-item",
        "light-extra",
        {
            "title": "Extra",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "requirements": ["R3"],
        },
        "## Description\n\nR3: Third behavior.",
    )
    result = world.run("orchestra", "analyze", PHASE)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "work-item-unknown-requirement" in result.stdout
