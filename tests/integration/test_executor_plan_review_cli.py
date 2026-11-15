from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping
from pathlib import Path

from conftest import REPO_ROOT, git

EFFORT = "derived-executor-review-effort"
PHASE = "derived-executor-review-phase"
PHASE_BODY = (
    "## Problem\n\nDerive executor mode at dispatch.\n\n"
    "## Requirements\n\nR1: A task plan without executor values passes review.\n\n"
    "## Approach\n\nUse the plan review workflow.\n\n"
    "## Exit criteria\n\nThe workflow advances to execute.\n"
)


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise AssertionError("expected a JSON object")
    return {key: item for key, item in value.items() if isinstance(key, str)}


def _string(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise AssertionError(f"expected string field {key}")
    return value


class World:
    def __init__(self: World, root: Path) -> None:
        self.repo = root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "test")
        git(self.repo, "commit", "--allow-empty", "-qm", "init")
        self.env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"ORCHESTRA_STORE", "CANON_STORE", "VIRTUAL_ENV"}
        }
        home = root / "home"
        home.mkdir()
        self.env["HOME"] = str(home)

    def run(self: World, tool: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--quiet", "--project", str(REPO_ROOT), tool, *args],
            capture_output=True,
            text=True,
            cwd=self.repo,
            env=self.env,
        )

    def ok(self: World, tool: str, *args: str) -> str:
        result = self.run(tool, *args)
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    def create(
        self: World, record_type: str, subject: str, payload: Mapping[str, object], body: str = ""
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

    def invoke(self: World, *args: str) -> dict[str, object]:
        return _object(json.loads(self.ok("orchestra", *args)))


def _phase_id(world: World) -> str:
    records = _object(
        json.loads(
            world.ok(
                "canon",
                "list",
                "--type",
                "score:phase",
                "--subject",
                PHASE,
                "--exact-subject",
                "--full",
            )
        )
    )["records"]
    if not isinstance(records, list) or not records:
        raise AssertionError("expected phase record")
    return _string(_object(records[0]), "id")


def _review(world: World, phase_id: str, step: str, authority: str) -> None:
    world.invoke(
        "workflow",
        "review",
        PHASE,
        step,
        "--artifact",
        phase_id,
        "--authority",
        authority,
        "--basis",
        f"Approved {step} under the test policy.",
        "--json",
    )


def test_plan_review_and_execute_gate_accepts_missing_executor(tmp_path: Path) -> None:
    world = World(tmp_path)
    (world.repo / "orchestra.toml").write_text(
        (REPO_ROOT / "orchestra.toml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    world.ok("canon", "init", "--schemas", "score,conductor,tuner,composer")
    world.create(
        "score:effort",
        EFFORT,
        {"goal": "Derived executor", "kind": "deliver", "autonomy": "auto-plan"},
    )
    world.create(
        "score:phase",
        PHASE,
        {"title": "Executor plan review", "ordinal": 1, "effort": EFFORT, "weight": "light"},
        PHASE_BODY,
    )
    world.create(
        "score:work-item",
        "task-without-executor",
        {
            "title": "Plan a task",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "size": "M",
            "estimate_minutes": 10,
            "requirements": ["R1"],
        },
        "## Description\n\nR1: Plan without a dispatch override.\n\n"
        "## Approach\n\nUse the approved design.",
    )
    world.create(
        "score:acceptance",
        "task-without-executor-check",
        {
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )

    preview = world.invoke("workflow", "preview", EFFORT, PHASE, "phase", "--json")
    run = _object(
        world.invoke(
            "workflow",
            "start",
            EFFORT,
            PHASE,
            "phase",
            "--snapshot-token",
            _string(preview, "snapshot_token"),
            "--json",
        )["run"]
    )
    phase_id = _phase_id(world)
    _review(world, phase_id, "spec", "user-approval")
    _review(world, phase_id, "design", "user-approval")
    _review(world, phase_id, "tasks", "task-plan-policy")

    actions = world.invoke("workflow", "next", _string(run, "subject"), "--json")["actions"]
    if not isinstance(actions, list) or not actions:
        raise AssertionError("expected the workflow to advance to execute")
    next_action = _object(actions[0])
    assert _string(next_action, "step") == "execute"
    assert _string(next_action, "state") == "ready"
