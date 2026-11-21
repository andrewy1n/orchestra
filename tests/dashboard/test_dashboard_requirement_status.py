from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from canon_support import create, make_project
from fastapi.testclient import TestClient

from dashboard.backend.server.app import create_app
from orchestra.canon.project import Project, open_store

EFFORT = "e"
PHASE = "p"
PHASE_BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n"
    "## Requirements\n\nR1: First behavior.\nR2: Second behavior.\n"
)


@pytest.fixture()
def project(tmp_path: Path) -> Project:
    project = make_project(tmp_path / "repo")
    create(project, "score:effort", EFFORT, {"goal": "G", "kind": "deliver"})
    phase = create(
        project,
        "score:phase",
        PHASE,
        {"title": "P", "ordinal": 1, "effort": EFFORT, "weight": "light"},
        PHASE_BODY,
    )
    project.update(phase["id"], record_type="score:phase", transition="in_progress")
    return project


def _acceptance(project: Project, subject: str, requirements: list[str]) -> str:
    record = create(
        project,
        "score:acceptance",
        subject,
        {
            "phase": PHASE,
            "effort": EFFORT,
            "requirements": requirements,
            "method": "check",
            "verify_command": "true",
        },
    )
    return record["id"]


def _run(project: Project, subject: str, acceptance_id: str, result: str) -> None:
    create(
        project,
        "tuner:check-run",
        subject,
        {
            "criterion_id": acceptance_id,
            "result": result,
            "revision": "abc",
            "effort": EFFORT,
            "method": "check",
            "signed_by": "",
        },
        "ok",
    )


def _client(project: Project) -> TestClient:
    return TestClient(create_app(open_store(project.project_root)), raise_server_exceptions=False)


def _statuses(client: TestClient) -> dict[str, str]:
    response = client.get("/api/phase", params={"effort": EFFORT, "phase": PHASE})
    assert response.status_code == 200, response.text
    rows = response.json()["detail"]["evidence"]["requirements"]
    return {row["id"]: row["status"] for row in rows}


def _detail_status(client: TestClient, requirement: str) -> str:
    response = client.get(
        "/api/requirement", params={"effort": EFFORT, "phase": PHASE, "id": requirement}
    )
    assert response.status_code == 200, response.text
    return response.json()["detail"]["status"]


def test_requirement_with_one_failed_acceptance_among_passes_shows_failed(
    project: Project,
) -> None:
    passing = _acceptance(project, "a-pass", ["R1"])
    failing = _acceptance(project, "a-fail", ["R1"])
    _run(project, "a-pass", passing, "pass")
    _run(project, "a-fail", failing, "fail")
    client = _client(project)
    assert _statuses(client)["R1"] == "failed"
    assert _detail_status(client, "R1") == "failed"


def test_requirement_with_a_linked_acceptance_missing_run_shows_unverified(
    project: Project,
) -> None:
    passing = _acceptance(project, "a-pass", ["R1"])
    _acceptance(project, "a-open", ["R1"])
    _run(project, "a-pass", passing, "pass")
    client = _client(project)
    assert _statuses(client)["R1"] == "unverified"
    assert _detail_status(client, "R1") == "unverified"


def test_requirement_with_no_acceptance_shows_unverified(project: Project) -> None:
    passing = _acceptance(project, "a-pass", ["R1"])
    _run(project, "a-pass", passing, "pass")
    client = _client(project)
    assert _statuses(client) == {"R1": "verified", "R2": "unverified"}
    assert _detail_status(client, "R2") == "unverified"
