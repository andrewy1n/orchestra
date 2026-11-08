from __future__ import annotations

import json
from pathlib import Path

import pytest
from canon_support import make_project

from orchestra.canon.project import Project
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
    assert preview["requested_steps"] == ["spec", "design", "tasks", "execute", "verify"]
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
