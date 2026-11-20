from __future__ import annotations

import json
from pathlib import Path

import pytest
from canon_support import make_project

from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.cli import main

EFFORT = "workflow-cli-effort"
PHASE_BODY = (
    "## Problem\nMeet the contract.\n"
    "## Requirements\nR1: Preserve the workflow contract.\n"
    "## Approach\nUse the reviewed design.\n"
    "## Exit criteria\nVerify the result.\n"
)


def _project(root: Path) -> tuple[Project, str]:
    project = make_project(root)
    project.create(
        record_type="score:effort",
        subject=EFFORT,
        payload={"goal": "Workflow CLI", "kind": "deliver"},
    )
    phase = project.create(
        record_type="score:phase",
        subject="phase-one",
        payload={"title": "Phase one", "ordinal": 1, "effort": EFFORT, "weight": "light"},
        body=PHASE_BODY,
    )
    return project, phase["id"]


def _invoke(root: Path, capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = main(["workflow", *args, "--store", str(root)])
    output = capsys.readouterr()
    return code, output.out, output.err


def test_preview_reports_scope_and_steps_before_start(tmp_path: Path, capsys) -> None:
    project, _ = _project(tmp_path)

    code, output, error = _invoke(
        tmp_path, capsys, "preview", EFFORT, "phase-one", "phase", "--json"
    )

    assert code == 0, output + error
    preview = json.loads(output)
    assert preview["phases"] == ["phase-one"]
    assert preview["requested_steps"] == ["spec", "design", "tasks", "execute", "verify", "land"]
    assert preview["prerequisites"] == {"phase-one": []}
    assert preview["snapshot_token"]
    assert not project.list("score:run")


def test_start_requires_the_preview_snapshot_and_status_resumes(tmp_path: Path, capsys) -> None:
    _, phase_id = _project(tmp_path)
    _, preview_output, _ = _invoke(
        tmp_path, capsys, "preview", EFFORT, "phase-one", "phase", "--json"
    )
    preview = json.loads(preview_output)
    code, output, error = _invoke(
        tmp_path,
        capsys,
        "start",
        EFFORT,
        "phase-one",
        "phase",
        "--snapshot-token",
        preview["snapshot_token"],
        "--json",
    )
    assert code == 0, output + error
    run = json.loads(output)["run"]

    code, output, error = _invoke(tmp_path, capsys, "next", run["subject"], "--json")
    assert code == 0, output + error
    assert json.loads(output)["actions"][0]["step"] == "spec"

    code, output, error = _invoke(
        tmp_path,
        capsys,
        "review",
        "phase-one",
        "spec",
        "--artifact",
        phase_id,
        "--authority",
        "user-approval",
        "--basis",
        "Approved by the user.",
        "--json",
    )
    assert code == 0, output + error
    assert json.loads(output)["review"]["payload"]["authority"] == "user-approval"

    code, output, error = _invoke(tmp_path, capsys, "status", run["subject"], "--json")
    assert code == 0, output + error
    status = json.loads(output)
    assert status["status"] == "incomplete"
    assert status["actions"][0]["step"] == "design"


def test_single_step_preview_and_analysis_stages_are_registered(tmp_path: Path, capsys) -> None:
    _project(tmp_path)

    code, output, error = _invoke(
        tmp_path, capsys, "preview", EFFORT, "phase-one", "design", "--json"
    )
    assert code == 0, output + error
    preview = json.loads(output)
    assert preview["operation"] == "single-step"
    assert preview["requested_steps"] == ["design"]

    code = main(["analyze", "phase-one", "--stage", "spec", "--json", "--store", str(tmp_path)])
    output = capsys.readouterr().out
    assert code == 0
    assert json.loads(output)["stage"] == "spec"

    code = main(["analyze", "phase-one", "--stage", "design", "--json", "--store", str(tmp_path)])
    output = capsys.readouterr().out
    assert code == 0
    assert json.loads(output)["stage"] == "design"


def test_unknown_run_and_stale_preview_return_errors(tmp_path: Path, capsys) -> None:
    project, _ = _project(tmp_path)
    _, preview_output, _ = _invoke(
        tmp_path, capsys, "preview", EFFORT, "phase-one", "phase", "--json"
    )
    preview = json.loads(preview_output)
    project.create(
        record_type="score:effort", subject="later", payload={"goal": "Later", "kind": "deliver"}
    )

    code, _, error = _invoke(
        tmp_path,
        capsys,
        "start",
        EFFORT,
        "phase-one",
        "phase",
        "--snapshot-token",
        preview["snapshot_token"],
        "--json",
    )
    assert code == 2
    assert "snapshot" in error.lower()

    code, _, error = _invoke(tmp_path, capsys, "next", "missing-run", "--json")
    assert code == 2
    assert "missing-run" in error


def _acceptance(project: Project, *, autonomy: str = "auto-plan", frozen: bool = False) -> Record:
    effort = project.resolve("score:effort", EFFORT)
    project.update(effort["id"], payload={"autonomy": autonomy})
    item = project.create(
        record_type="score:work-item",
        subject="build-wheel",
        payload={
            "title": "Build wheel",
            "phase": "phase-one",
            "effort": EFFORT,
            "kind": "deliver",
            "assignee": "",
        },
        body="## Description\n\nVerify the wheel.",
    )
    project.update(item["id"], transition="in_progress")
    return project.create(
        record_type="score:acceptance",
        subject="build-wheel",
        payload={
            "phase": "phase-one",
            "effort": EFFORT,
            "method": "tdd",
            "requirement": "R1",
            "verify_command": "pytest tests/test_wheel.py::test_install",
            **(
                {
                    "oracle_policy": "frozen",
                    "test_ids": ["tests/test_wheel.py::test_install"],
                    "oracle_hashes": ["tests/test_wheel.py:sha256:" + "0" * 64],
                }
                if frozen
                else {"oracle_policy": "none"}
            ),
        },
    )


@pytest.mark.parametrize("mode", ["method", "command"])
def test_workflow_amend_check_preserves_requirement_and_records_reason(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], mode: str
) -> None:
    project, _ = _project(tmp_path)
    acceptance = _acceptance(project)
    new_command = "pytest tests/packaging/test_wheel.py::test_install"
    change = (
        ["--routine-check", "packaging"]
        if mode == "method"
        else ["--equivalent-command", new_command]
    )

    code, output, error = _invoke(
        tmp_path,
        capsys,
        "amend-check",
        acceptance["id"],
        "--expected-revision",
        acceptance["revision"],
        "--basis",
        "The wheel install test exercises the same assertion.",
        *change,
    )

    assert code == 0, error
    current = project.resolve("score:acceptance", "build-wheel")
    assert output.strip() == current["id"]
    assert current["payload"]["requirement"] == "R1"
    if mode == "method":
        assert current["id"] != acceptance["id"]
        assert current["payload"]["method"] == "check"
        assert current["payload"]["verify_command"] == acceptance["payload"]["verify_command"]
        assert project.get(acceptance["id"])["lifecycle_state"] == "superseded"
    else:
        assert current["id"] == acceptance["id"]
        assert current["payload"]["method"] == "tdd"
        assert current["payload"]["verify_command"] == new_command
    amendment = project.list("conductor:assignment-amendment")[0]
    assert amendment["payload"]["work_item"] == "build-wheel"
    assert "same assertion" in amendment.get("body", "")


@pytest.mark.parametrize(
    ("autonomy", "frozen", "reason"),
    [("gated", False, "require auto-plan"), ("auto-phases", True, "frozen")],
)
def test_workflow_amend_check_refuses_gated_or_frozen_changes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    autonomy: str,
    frozen: bool,
    reason: str,
) -> None:
    project, _ = _project(tmp_path)
    acceptance = _acceptance(project, autonomy=autonomy, frozen=frozen)

    code, _, error = _invoke(
        tmp_path,
        capsys,
        "amend-check",
        acceptance["id"],
        "--expected-revision",
        acceptance["revision"],
        "--basis",
        "Routine packaging verification.",
        "--routine-check",
        "packaging",
    )

    assert code == 2
    assert reason in error
    assert project.get(acceptance["id"]) == acceptance
    assert not project.list("conductor:assignment-amendment")
