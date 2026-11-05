"""A two-wave phase runs through `wave start`, `task land`, and `wave end` via the installed entry points."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping
from pathlib import Path

import pytest
from conftest import REPO_ROOT, git, make_git_repo

PHASE = "dc-phase"
EFFORT = "dc-effort"
PHASE_BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n"
    f"## Landing\n\nbranch: phase/{PHASE}\nworktree: <repo>/.worktrees/{PHASE}\nbase: main\n"
)


class World:
    def __init__(self, root: Path) -> None:
        self.repo = make_git_repo()
        git(self.repo, "branch", "-M", "main")
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
            cwd=str(self.repo),
            env=self.env,
        )

    def ok(self, tool: str, *args: str) -> str:
        result = self.run(tool, *args)
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    def create(
        self, record_type: str, subject: str, payload: Mapping[str, object], body: str
    ) -> None:
        self.ok(
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

    def task(self, slug: str, depends_on: list[str]) -> None:
        payload: dict[str, object] = {
            "title": slug,
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
            "depends_on": depends_on,
        }
        self.create("score:work-item", slug, payload, "## Description\n\nd\n\n## Approach\n\na")
        accept = {"method": "check", "phase": PHASE, "effort": EFFORT, "verify_command": "true"}
        self.create("score:acceptance", slug, accept, "")

    def land(self, slug: str) -> dict[str, object]:
        evidence = self.repo / f"{slug}.evidence.json"
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
        return json.loads(
            self.ok("orchestra", "task", "land", slug, "--evidence", str(evidence), "--json")
        )

    def state(self, slug: str) -> str:
        out = self.ok(
            "canon", "list", "--type", "score:work-item", "--subject", slug, "--exact-subject",
            "--format", "tsv", "--fields", "lifecycle_state",
        )  # fmt: skip
        return out.splitlines()[-1]


@pytest.fixture
def world(tmp_path: Path) -> World:
    world = World(tmp_path)
    world.ok("canon", "init", "--schemas", "score,conductor,tuner,composer")
    world.create("score:effort", EFFORT, {"goal": "g", "kind": "deliver"}, "")
    phase = {"title": PHASE, "ordinal": 1, "effort": EFFORT}
    world.create("score:phase", PHASE, phase, PHASE_BODY)
    git(world.repo, "branch", f"phase/{PHASE}", "main")
    git(
        world.repo,
        "worktree",
        "add",
        "-q",
        str(world.repo / ".worktrees" / PHASE),
        f"phase/{PHASE}",
    )
    for slug, deps in (("t1", []), ("t2", []), ("verify-dc", ["t1", "t2"])):
        world.task(slug, deps)
    return world


def test_two_wave_phase_runs_through_the_three_verbs(world: World) -> None:
    first = json.loads(world.ok("orchestra", "wave", "start", PHASE, "--json"))
    assert [t["task"] for t in first["tasks"]] == ["t1", "t2"]
    for task in first["tasks"]:
        (Path(task["write_root"]) / f"{task['task']}.txt").write_text("work\n")
        landed = world.land(task["task"])
        assert landed["state"] == "done"
        assert landed["commit"]
    ended = json.loads(world.ok("orchestra", "wave", "end", PHASE, "--json"))
    assert ended["merged"] == ["t1", "t2"]
    second = json.loads(world.ok("orchestra", "wave", "start", PHASE, "--json"))
    assert [t["task"] for t in second["tasks"]] == ["verify-dc"]
    assert second["tasks"][0]["write_root"] == str(world.repo / ".worktrees" / PHASE)
    assert world.land("verify-dc")["state"] == "done"
    tree = world.repo / ".worktrees" / PHASE
    assert (tree / "t1.txt").exists() and (tree / "t2.txt").exists()
    for slug in ("t1", "t2", "verify-dc"):
        assert world.state(slug) == "done"
