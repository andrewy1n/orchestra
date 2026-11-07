from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import REPO_ROOT
from test_verification_methods import (
    NODE,
    PROBE,
    close_request,
    green,
    run_acceptance,
    setup_acceptance,
)

from orchestra.canon import record
from orchestra.canon.project import Project
from orchestra.canon.sqlite_backend import SqliteBackend
from orchestra.canon.types import JsonObject, Record
from orchestra.derive import release_ready


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
    (tmp_path / "test_probe.py").write_text(PROBE)
    result = _close_cli(project, acceptance, green(project, acceptance), red)
    assert result.returncode == 2
    assert "assertion-level red" in result.stderr


def test_task_land_closes_unfrozen_tdd_with_recorded_red(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    ids = iter(
        ["rec-ffffffff-ffff-4fff-8fff-ffffffffffff", "rec-00000000-0000-4000-8000-000000000000"]
    )

    def next_id(_store: SqliteBackend) -> str:
        return next(ids)

    def same_time() -> str:
        return acceptance["recorded_at"]

    with monkeypatch.context() as clock:
        clock.setattr(SqliteBackend, "new_id", next_id)
        clock.setattr(record, "now", same_time)
        red = run_acceptance(project, acceptance)
        passed = green(project, acceptance)
    assert red["recorded_at"] == passed["recorded_at"]
    assert red["id"] > passed["id"]
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


def test_task_land_closes_a_phase_with_mixed_methods_and_policies(tmp_path: Path) -> None:
    project, first = setup_acceptance(tmp_path, "tdd", "none")
    phase = project.list("score:phase")[0]
    requirements = ["R1", "R2", "R3", "R4"]
    body = "## Problem\n\nMixed proof.\n\n## Approach\n\nCheck each contract.\n\n## Exit criteria\n\nAll pass.\n\n## Requirements\n\n"
    body += "\n".join(f"{rid}: Contract {rid} passes." for rid in requirements)
    project.update(phase["id"], payload={"weight": "light"}, body=body)
    first = project.update(first["id"], payload={"requirement": "R1"})
    acceptances = [first]
    for i, (method, policy) in enumerate(
        [("check", "none"), ("tdd", "frozen"), ("check", "frozen")], start=2
    ):
        payload: JsonObject = {
            "method": method,
            "oracle_policy": policy,
            "phase": "p1",
            "effort": "alpha",
            "verify_command": first["payload"]["verify_command"],
            "requirement": f"R{i}",
        }
        if policy == "frozen":
            payload["test_ids"] = [NODE]
            payload["oracle_hashes"] = [
                "test_probe.py:sha256:" + hashlib.sha256(PROBE.encode()).hexdigest()
            ]
        acceptances.append(
            project.create(
                record_type="score:acceptance", subject=f"probe-contract-{i}", payload=payload
            )
        )
    item = _task(project)
    task_payload: JsonObject = {"requirements": [*requirements], "write_root": str(tmp_path)}
    project.update(item["id"], payload=task_payload)
    for acceptance in acceptances:
        if acceptance["payload"]["method"] == "tdd":
            assert run_acceptance(project, acceptance)["payload"]["result"] == "fail"
    passed = green(project, first)
    path = tmp_path.with_suffix(".mixed-evidence.json")
    path.write_text(
        json.dumps(
            {
                "subject": "probe",
                "kind": "repair",
                "result": "pass",
                "verdict": "pass",
                "evidence": "Run all four contracts in one phase.",
            }
        )
    )
    result = _cli(tmp_path, "task", "land", "probe", "--evidence", str(path), "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["state"] == "done"
    assert project.get(item["id"])["lifecycle_state"] == "done"
    revision = passed["payload"]["revision"]
    assert isinstance(revision, str)
    assert release_ready(project.records(), "p1", head=revision)
