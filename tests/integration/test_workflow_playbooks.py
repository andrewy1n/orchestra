from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping
from pathlib import Path

import pytest
from conftest import REPO_ROOT, git, make_git_repo

EFFORT = "workflow-playbook-effort"
PHASE_BODY = (
    "## Problem\n\np\n\n"
    "## Requirements\n\nR1: Preserve the workflow behavior.\n\n"
    "## Approach\n\nUse the reviewed workflow.\n\n"
    "## Exit criteria\n\nVerify the result.\n"
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


def _first_action(record: Mapping[str, object]) -> dict[str, object]:
    actions = record.get("actions")
    if not isinstance(actions, list) or not actions:
        raise AssertionError("expected at least one action")
    return _object(actions[0])


class World:
    def __init__(self, root: Path) -> None:
        self.repo = make_git_repo()
        git(self.repo, "branch", "-M", "main")
        self.env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"ORCHESTRA_STORE", "CANON_STORE", "VIRTUAL_ENV"}
        }
        home = root / "home"
        home.mkdir()
        self.env["HOME"] = str(home)

    def run(self, tool: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--quiet", "--project", str(REPO_ROOT), tool, *args],
            capture_output=True,
            text=True,
            cwd=self.repo,
            env=self.env,
        )

    def ok(self, tool: str, *args: str) -> str:
        result = self.run(tool, *args)
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    def create(
        self, record_type: str, subject: str, payload: Mapping[str, object], body: str = ""
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

    def invoke(self, *args: str) -> dict[str, object]:
        return _object(json.loads(self.ok("orchestra", *args)))


@pytest.fixture
def world(tmp_path: Path) -> World:
    result = World(tmp_path)
    result.ok("canon", "init", "--schemas", "score,conductor,tuner,composer")
    result.create("score:effort", EFFORT, {"goal": "Playbooks", "kind": "deliver"})
    result.create(
        "score:phase",
        "phase-one",
        {"title": "Phase one", "ordinal": 1, "effort": EFFORT, "weight": "light"},
        PHASE_BODY,
    )
    result.create(
        "score:phase",
        "phase-two",
        {
            "title": "Phase two",
            "ordinal": 2,
            "effort": EFFORT,
            "weight": "light",
            "depends_on": ["phase-one"],
        },
        PHASE_BODY,
    )
    result.create(
        "score:work-item",
        "task-one",
        {
            "title": "Task one",
            "phase": "phase-one",
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "requirements": ["R1"],
        },
        "## Description\n\nImplement R1.",
    )
    result.create(
        "score:acceptance",
        "acceptance-one",
        {
            "method": "check",
            "phase": "phase-one",
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    return result


def _review(world: World, phase: str, step: str) -> None:
    phase_record = _object(
        json.loads(
            world.ok(
                "canon",
                "list",
                "--type",
                "score:phase",
                "--subject",
                phase,
                "--exact-subject",
                "--full",
            )
        )["records"][0]
    )
    world.invoke(
        "workflow",
        "review",
        phase,
        step,
        "--artifact",
        _string(phase_record, "id"),
        "--authority",
        "user-approval",
        "--basis",
        f"Approved {step}.",
        "--json",
    )


def test_phase_playbook_resumes_from_records_and_advances_after_integration(world: World) -> None:
    preview = world.invoke("workflow", "preview", EFFORT, "phase-one", "phase", "--json")
    run = _object(
        world.invoke(
            "workflow",
            "start",
            EFFORT,
            "phase-one",
            "phase",
            "--snapshot-token",
            _string(preview, "snapshot_token"),
            "--json",
        )["run"]
    )

    assert (
        _string(
            _first_action(world.invoke("workflow", "next", _string(run, "subject"), "--json")),
            "step",
        )
        == "spec"
    )
    _review(world, "phase-one", "spec")
    assert (
        _string(
            _first_action(world.invoke("workflow", "status", _string(run, "subject"), "--json")),
            "step",
        )
        == "design"
    )
    _review(world, "phase-one", "design")
    assert (
        _string(
            _first_action(world.invoke("workflow", "next", _string(run, "subject"), "--json")),
            "step",
        )
        == "tasks"
    )
    _review(world, "phase-one", "tasks")

    task = _object(
        json.loads(
            world.ok(
                "canon",
                "list",
                "--type",
                "score:work-item",
                "--subject",
                "task-one",
                "--exact-subject",
                "--full",
            )
        )["records"][0]
    )
    world.ok(
        "canon",
        "update",
        "--type",
        "score:work-item",
        "--id",
        _string(task, "id"),
        "--transition",
        "in_progress",
    )
    world.ok(
        "canon",
        "update",
        "--type",
        "score:work-item",
        "--id",
        _string(task, "id"),
        "--transition",
        "done",
    )
    world.create(
        "conductor:execution-report",
        "task-one",
        {
            "work_item": "task-one",
            "result": "pass",
            "verdict": "pass",
            "revision": "deadbeef",
            "effort": EFFORT,
        },
    )
    world.create(
        "conductor:integration-report",
        "phase-one-integration",
        {"phase": "phase-one", "effort": EFFORT, "result": "pass", "revision": "deadbeef"},
        "## Interfaces\n\nReviewed.\n\n## Assumptions\n\nReviewed.\n\n## Invariants\n\nReviewed.\n\n## Conflicts\n\nNone.",
    )
    status = world.invoke("workflow", "status", _string(run, "subject"), "--json")
    assert status["status"] == "incomplete"
    assert _string(_first_action(status), "step") == "verify"
    assert (
        _string(
            _first_action(world.invoke("workflow", "next", _string(run, "subject"), "--json")),
            "step",
        )
        == "verify"
    )


def test_deliver_playbook_keeps_external_prerequisite_out_of_scope(world: World) -> None:
    preview = world.invoke("workflow", "preview", EFFORT, "phase-two", "deliver", "--json")
    assert preview["phases"] == ["phase-two"]
    assert preview["external_dependencies"] == ["phase-one"]
    run = _object(
        world.invoke(
            "workflow",
            "start",
            EFFORT,
            "phase-two",
            "deliver",
            "--snapshot-token",
            _string(preview, "snapshot_token"),
            "--json",
        )["run"]
    )

    action = _first_action(world.invoke("workflow", "next", _string(run, "subject"), "--json"))

    assert _string(action, "state") == "blocked"
    assert "phase-one" in _string(action, "reason")
