from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from helpers import generic_body, schema_defs

from dashboard.backend.server.app import create_app
from interfaces.interfaces_support import build_store, run_cli
from orchestra.canon.project import Project, open_store
from orchestra.canon.sections import body_section, body_section_ci

SPEC_BODY = (
    "## REQUIREMENTS\n\nR1: heading case does not matter.\n\n## Requirements\n\nR1: stored text.\n\n"
    + "\n\n".join(
        f"## {name}\n\nplaceholder text."
        for name in (
            "Acceptance criteria",
            "Constraints",
            "Non-goals",
            "Invariants",
            "Assumptions",
        )
    )
    + "\n"
)


def _create(
    root: Path, record_type: str, subject: str, payload: dict[str, object], body: str = ""
) -> None:
    args = ["create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)]
    text = body or generic_body(schema_defs()[record_type])
    if text:
        args.extend(["--body", text])
    result = run_cli(*args, root=root)
    assert result.returncode == 0, result.stdout + result.stderr


def _seed(root: Path) -> str:
    _create(root, "score:effort", "alpha", {"goal": "ship alpha", "kind": "deliver"})
    _create(root, "score:phase", "p-one", {"title": "first phase", "ordinal": 1, "effort": "alpha"})
    _create(
        root,
        "score:work-item",
        "t-one",
        {
            "title": "first task",
            "phase": "p-one",
            "kind": "deliver",
            "assignee": "",
            "effort": "alpha",
            "requirements": ["R1"],
        },
    )
    _create(
        root,
        "score:specification",
        "p-one-spec",
        {"weight": "full", "phase": "p-one", "effort": "alpha", "requirements": ["R1"]},
        SPEC_BODY,
    )
    task = json.loads(run_cli("list", "--type", "score:work-item", root=root).stdout)["records"][0]
    _create(
        root,
        "conductor:assignment",
        "t-one-a1",
        {"work_item": "t-one", "executor": "subagent", "effort": "alpha"},
        "## orientation\n\nread the brief first.\n\n## Orientation\n\nstored text.\n",
    )
    _create(
        root,
        "conductor:assignment-amendment",
        "t-one-m1",
        {"assignment": "t-one-a1", "work_item": "t-one", "effort": "alpha"},
        "## CORRECTION\n\nuse the owner module.\n\n## Correction\n\nstored text.\n",
    )
    return task["id"]


@pytest.fixture(scope="module")
def served() -> Iterator[tuple[TestClient, str]]:
    root = build_store()
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("ORCHESTRA_SIGNED_BY", "route-signer")
        try:
            task_id = _seed(root)
            project: Project = open_store(root)
            yield TestClient(create_app(project), raise_server_exceptions=False), task_id
        finally:
            shutil.rmtree(root, ignore_errors=True)


def test_body_section_ci_matches_heading_in_any_case() -> None:
    body = "## ORIENTATION\n\nfirst\n\n## other\n\nsecond\n"
    assert body_section_ci(body, "Orientation") == "first"
    assert body_section(body, "Orientation") == ""


def test_task_route_reads_orientation_and_correction_in_any_case(
    served: tuple[TestClient, str],
) -> None:
    client, task_id = served
    response = client.get("/api/task", params={"id": task_id})
    assert response.status_code == 200
    (work,) = response.json()["detail"]["agent_work"]
    assert work["assignment"]["orientation"] == "read the brief first."
    assert [row["correction"] for row in work["amendments"]] == ["use the owner module."]


def test_journal_route_reads_correction_in_any_case(served: tuple[TestClient, str]) -> None:
    client, _task_id = served
    body = client.get("/api/journal", params={"effort": "alpha"}).json()
    texts = [item["text"] for item in [*body["open"], *body["rest"]]]
    assert texts == ["use the owner module. · t-one"]


def test_requirement_route_reads_requirements_in_any_case(
    served: tuple[TestClient, str],
) -> None:
    client, _task_id = served
    response = client.get(
        "/api/requirement", params={"effort": "alpha", "phase": "p-one", "id": "R1"}
    )
    assert response.status_code == 200
    assert response.json()["detail"]["text"] == "heading case does not matter."
