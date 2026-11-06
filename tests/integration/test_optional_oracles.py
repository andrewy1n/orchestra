from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import REPO_ROOT
from test_verification_methods import close_request, green, run_acceptance, setup_acceptance

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record


def _cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *args],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        capture_output=True,
        text=True,
    )


def _task(project: Project) -> Record:
    item = project.create(
        record_type="score:work-item",
        subject="probe",
        payload={
            "title": "Probe",
            "kind": "repair",
            "assignee": "inline",
            "phase": "p1",
            "effort": "alpha",
        },
        body="## Description\n\nProbe.\n\n## Approach\n\nCheck the policy.",
    )
    return project.update(item["id"], transition="in_progress")


def _close_cli(
    project: Project, acceptance: Record, passed: Record, red: Record | None = None
) -> subprocess.CompletedProcess[str]:
    item = _task(project)
    request = close_request(acceptance, passed, red)
    request["work_item_id"] = item["id"]
    path = project.project_root.with_suffix(".request.json")
    path.write_text(json.dumps(request))
    return _cli(
        project.project_root,
        "close-batch",
        "--input",
        str(path),
        "--cwd",
        str(project.project_root),
    )


@pytest.mark.parametrize(
    ("method", "policy"),
    [("tdd", "none"), ("check", "none"), ("tdd", "frozen"), ("check", "frozen")],
)
def test_cli_closes_the_method_policy_matrix(tmp_path: Path, method: str, policy: str) -> None:
    project, acceptance = setup_acceptance(tmp_path, method, policy, frozen=policy == "frozen")
    red = run_acceptance(project, acceptance) if method == "tdd" else None
    passed = green(project, acceptance)
    result = _close_cli(project, acceptance, passed, red)
    assert result.returncode == 0, result.stderr
    batch = tmp_path.with_suffix(".ndjson")
    batch.write_text(result.stdout)
    applied = subprocess.run(
        [sys.executable, "-m", "orchestra.canon", "apply", str(batch)],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        capture_output=True,
        text=True,
    )
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert json.loads(applied.stdout)["ok"]
    assert project.list("score:work-item")[0]["lifecycle_state"] == "done"


def test_cli_refuses_pass_only_unfrozen_tdd(tmp_path: Path) -> None:
    project, acceptance = setup_acceptance(tmp_path, "tdd", "none")
    result = _close_cli(project, acceptance, green(project, acceptance))
    assert result.returncode == 2
    assert "red_check_run_id" in result.stderr
    assert project.list("score:work-item")[0]["lifecycle_state"] == "in_progress"


def test_cli_refuses_hash_drift_for_frozen_check(tmp_path: Path) -> None:
    project, acceptance = setup_acceptance(tmp_path, "check", "frozen", frozen=True)
    (tmp_path / "test_probe.py").write_text("def test_probe():\n    assert True\n")
    result = _close_cli(project, acceptance, green(project, acceptance))
    assert result.returncode == 2
    assert "hash drift" in result.stderr


def test_cli_refuses_import_only_red_for_frozen_tdd(tmp_path: Path) -> None:
    project, acceptance = setup_acceptance(tmp_path, "tdd", "frozen", frozen=True)
    (tmp_path / "test_probe.py").write_text("import missing_oracle_module\n")
    red = run_acceptance(project, acceptance)
    from test_verification_methods import PROBE

    (tmp_path / "test_probe.py").write_text(PROBE)
    result = _close_cli(project, acceptance, green(project, acceptance), red)
    assert result.returncode == 2
    assert "assertion-level red" in result.stderr


def test_task_land_closes_unfrozen_tdd_with_recorded_red(tmp_path: Path) -> None:
    project, acceptance = setup_acceptance(tmp_path, "tdd", "none")
    phase = project.list("score:phase")[0]
    project.update(
        phase["id"],
        payload={"weight": "light"},
        body="## Problem\n\nP.\n\n## Approach\n\nA.\n\n## Exit criteria\n\nE.\n\n## Requirements\n\nR1: Probe passes.",
    )
    item = _task(project)
    project.update(item["id"], payload={"requirements": ["R1"], "write_root": str(tmp_path)})
    acceptance = project.update(acceptance["id"], payload={"requirement": "R1"})
    run_acceptance(project, acceptance)
    green(project, acceptance)
    evidence: JsonObject = {
        "subject": "probe",
        "kind": "repair",
        "result": "pass",
        "verdict": "pass",
        "evidence": "Run the probe through the production runner.",
    }
    evidence_path = tmp_path.with_suffix(".evidence.json")
    evidence_path.write_text(json.dumps(evidence))
    result = _cli(tmp_path, "task", "land", "probe", "--evidence", str(evidence_path), "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["state"] == "done"
    assert project.get(item["id"])["lifecycle_state"] == "done"
