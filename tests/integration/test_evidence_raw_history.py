from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from canon_support import REPO, create, make_project

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record

EFFORT = "ef"


def _canon(project: Project, *argv: str) -> object:
    result = subprocess.run(
        [sys.executable, "-m", "orchestra.canon", "--root", str(project.project_root), *argv],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def _without_derived(record: object) -> JsonObject:
    assert isinstance(record, dict)
    return {key: value for key, value in record.items() if key != "derived"}


def _stored(project: Project, record_id: str) -> JsonObject:
    return _without_derived(project.get(record_id))


def _listed(project: Project, record_type: str) -> dict[str, JsonObject]:
    listing = _canon(project, "list", "--type", record_type, "--full")
    assert isinstance(listing, dict)
    rows = listing["records"]
    assert isinstance(rows, list)
    return {row["id"]: _without_derived(row) for row in rows}


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(project, "score:phase", "ph", {"title": "Ph", "ordinal": 1, "effort": EFFORT})
    return project


def _check_run_payload(result: str) -> JsonObject:
    return {
        "criterion_id": "acc-1",
        "method": "check",
        "effort": EFFORT,
        "revision": "a1b2c3d",
        "result": result,
        "signed_by": "",
    }


def test_r17_get_and_list_return_corrected_check_run_chain_unchanged(project: Project) -> None:
    original = create(project, "tuner:check-run", "acc-1", _check_run_payload("fail"))
    corrected = project.correct(original["id"], payload={"result": "pass"})["record"]

    for record in (original, corrected):
        assert _without_derived(_canon(project, "get", "--id", record["id"])) == _stored(
            project, record["id"]
        )
    listed = _listed(project, "tuner:check-run")
    assert set(listed) == {original["id"], corrected["id"]}
    for record_id, row in listed.items():
        assert row == _stored(project, record_id)
    assert listed[original["id"]]["payload"] == _check_run_payload("fail")
    assert listed[corrected["id"]]["relationships"] == {"corrects": [original["id"]]}


def test_r17_get_and_list_return_superseded_acceptance_unchanged(project: Project) -> None:
    payload: JsonObject = {
        "effort": EFFORT,
        "phase": "ph",
        "method": "check",
        "verify_command": "true",
        "requirement": "R1",
    }
    old: Record = create(project, "score:acceptance", "acc-1", payload)
    new = project.supersede(old["id"], payload={"verify_command": "false"})["record"]

    got = _without_derived(_canon(project, "get", "--id", old["id"]))

    assert got == _stored(project, old["id"])
    assert got["lifecycle_state"] == "superseded"
    assert got["payload"] == payload
    listed = _listed(project, "score:acceptance")
    assert set(listed) == {old["id"], new["id"]}
    for record_id, row in listed.items():
        assert row == _stored(project, record_id)
