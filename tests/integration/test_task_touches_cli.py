from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import make_git_repo

PHASE = "touches-cli"
EFFORT = "touches-effort"


class World:
    def __init__(self, root: Path) -> None:
        self.store = make_git_repo()
        self.env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"ORCHESTRA_STORE", "CANON_STORE", "VIRTUAL_ENV"}
        }
        self.env["HOME"] = str(root / "home")
        (root / "home").mkdir()

    def run(self, tool: str, *args: str) -> subprocess.CompletedProcess[str]:
        module = "orchestra.canon" if tool == "canon" else "orchestra.cli"
        return subprocess.run(
            [sys.executable, "-m", module, *args],
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


@pytest.fixture
def world(tmp_path: Path) -> World:
    world = World(tmp_path)
    result = world.run("canon", "init", "--schemas", "score,conductor,tuner,composer")
    assert result.returncode == 0, result.stdout + result.stderr
    world.create("score:effort", EFFORT, {"goal": "Plan work", "kind": "deliver"}, "")
    world.create(
        "score:phase",
        PHASE,
        {"title": PHASE, "ordinal": 1, "effort": EFFORT, "weight": "light"},
        "## Problem\n\nPlan work.\n\n## Approach\n\nRun tasks.\n\n"
        "## Exit criteria\n\nDetect scope conflicts.\n\n"
        "## Requirements\n\nR1: Detect overlapping write scopes.\n",
    )
    world.create(
        "score:acceptance",
        "touches-cli-check",
        {
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
        "",
    )
    return world


def add_item(
    world: World,
    subject: str,
    *,
    touches: list[object] | None,
    size: str = "M",
    depends_on: list[str] | None = None,
) -> None:
    payload: dict[str, object] = {
        "title": subject,
        "phase": PHASE,
        "kind": "deliver",
        "assignee": "",
        "effort": EFFORT,
        "requirements": ["R1"],
        "size": size,
        "depends_on": depends_on or [],
    }
    if touches is not None:
        payload["touches"] = touches
    world.create(
        "score:work-item",
        subject,
        payload,
        "## Description\n\nImplement the task.\n",
    )


def _findings(world: World) -> tuple[int, list[dict[str, object]], str]:
    result = world.run("orchestra", "analyze", PHASE, "--json")
    assert result.stdout.strip(), result.stderr
    report = json.loads(result.stdout)
    return result.returncode, report["findings"], result.stdout


def test_r3_r4_literal_glob_overlap_is_advisory_and_filesystem_independent(world: World) -> None:
    add_item(world, "left", touches=["missing-output/*.py"])
    add_item(world, "right", touches=["missing-output/main.py"])
    assert not (world.store / "missing-output").exists()

    before = world.run("canon", "list", "--type", "score:work-item", "--format", "json")
    code, findings, output = _findings(world)
    after = world.run("canon", "list", "--type", "score:work-item", "--format", "json")

    warnings = [finding for finding in findings if finding["code"] == "touches-overlap"]
    assert code == 0, output
    assert len(warnings) == 1
    warning = warnings[0]
    assert warning["severity"] == "warning"
    assert warning["subject"] == "left, right"
    assert all(
        value in str(warning["message"])
        for value in ("missing-output/*.py", "missing-output/main.py", "missing-output/main.py")
    )
    assert json.loads(before.stdout) == json.loads(after.stdout)


def test_nonexistent_literal_outputs_still_conflict(world: World) -> None:
    path = world.store / "not-created" / "output.py"
    add_item(world, "left", touches=["not-created/output.py"])
    add_item(world, "right", touches=["not-created/output.py"])

    code, findings, output = _findings(world)

    assert not path.exists()
    assert code == 0, output
    assert any(
        finding["code"] == "touches-overlap" and "not-created/output.py" in str(finding["message"])
        for finding in findings
    )


def test_globstar_zero_directories_and_glob_glob_overlap_have_a_witness(world: World) -> None:
    add_item(world, "left", touches=["src/**/main.py"])
    add_item(world, "right", touches=["src/*.py"])

    code, findings, output = _findings(world)

    assert code == 0, output
    assert any(
        finding["code"] == "touches-overlap" and "src/main.py" in str(finding["message"])
        for finding in findings
    )


def test_direct_dependency_small_tasks_report_merge_candidate(world: World) -> None:
    add_item(world, "first", touches=["src/*.py"], size="S")
    add_item(world, "second", touches=["src/main.py"], size="XS", depends_on=["first"])

    code, findings, output = _findings(world)

    assert code == 0, output
    assert any(
        finding["code"] == "touches-merge-candidate" and finding["subject"] == "first, second"
        for finding in findings
    )


def test_direct_dependency_with_medium_task_is_not_a_merge_candidate(world: World) -> None:
    add_item(world, "first", touches=["src/*.py"], size="M")
    add_item(world, "second", touches=["src/main.py"], size="S", depends_on=["first"])

    code, findings, output = _findings(world)

    assert code == 0, output
    assert not any(finding["code"] == "touches-merge-candidate" for finding in findings)


@pytest.mark.parametrize("touches", [None, []])
def test_missing_or_empty_scope_is_not_compared_as_disjoint(
    world: World, touches: list[object] | None
) -> None:
    add_item(world, "unknown", touches=touches)
    add_item(world, "scoped", touches=["src/*.py"])

    code, findings, output = _findings(world)

    assert code == 0, output
    assert not any(
        finding["code"] in {"touches-overlap", "touches-invalid"} for finding in findings
    )


def test_invalid_pattern_is_a_visible_error(world: World) -> None:
    add_item(world, "invalid", touches=["src//main.py"])

    code, findings, output = _findings(world)

    assert code == 1, output
    assert any(finding["code"] == "touches-invalid" for finding in findings)
