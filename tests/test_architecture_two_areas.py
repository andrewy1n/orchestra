from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from canon_support import make_project
from conftest import REPO_ROOT
from fastapi.testclient import TestClient
from interfaces.interfaces_support import invoke

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend.server.app import create_app
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.verification.standing_constraints import criterion_id
from orchestra.views.architecture import architecture_view, render_architecture

HEAD = "a" * 40
EFFORT = "two-area-effort"

SCOPES = [
    ("area", "composer"),
    ("component", "records"),
    ("interface", "record-api"),
    ("area", "interfaces"),
    ("component", "views"),
]


def _component(project: Project, name: str, area: str) -> Record:
    return project.create(
        record_type="composer:component",
        subject=name,
        payload={"area": area},
        body=f"## Responsibility\nOwns {name} duties.\n",
    )


def _decision(
    project: Project, title: str, affects: list[str], status: str, rationale: str
) -> Record:
    payload: JsonObject = {"status": status, "affects": list(affects)}
    return project.create(
        record_type="composer:architecture-decision",
        subject=title,
        payload=payload,
        body=f"## Rationale\n{rationale}\n",
    )


def _constraint(project: Project, name: str, rule: str, targets: list[str]) -> Record:
    return project.create(
        record_type="score:standing-constraint",
        subject=name,
        payload={
            "area": "composer",
            "rule": rule,
            "check": f"scripts/{name}",
            "targets": list(targets),
        },
        body="## Basis\nIsolation.\n",
    )


def _project(root: Path) -> Project:
    project = make_project(root)
    project.create(
        record_type="score:effort", subject=EFFORT, payload={"goal": "Arch", "kind": "deliver"}
    )
    _component(project, "records", "composer")
    _component(project, "views", "interfaces")
    project.create(
        record_type="composer:interface",
        subject="record-api",
        payload={"connects": ["records"]},
        body="## Provides\nServes record-api callers.\n",
    )
    project.create(
        record_type="composer:interface",
        subject="view-api",
        payload={"connects": ["views"]},
        body="## Provides\nServes view-api callers.\n",
    )
    _decision(project, "typed-records", ["records"], "accepted", "Typed rows keep reads cheap.")
    _decision(project, "shard-records", ["records"], "proposed", "Sharding scales later.")
    _decision(project, "versioned-api", ["record-api"], "accepted", "Clients pin versions.")
    _decision(project, "markdown-views", ["views"], "accepted", "Markdown diffs cleanly.")
    _decision(project, "paged-views", ["views"], "proposed", "Paging bounds output.")
    adapters = _constraint(project, "adapters-only", "Only adapters touch the store.", ["records"])
    _constraint(project, "views-pure", "Renderers stay read-only.", ["views"])
    project.create(
        record_type="tuner:check-run",
        subject="adapters-only-check",
        payload={
            "criterion_id": criterion_id(adapters["id"]),
            "revision": HEAD,
            "result": "pass",
            "effort": EFFORT,
            "method": "check",
            "runner": "orchestra",
            "signed_by": "",
        },
    )
    return project


def _cli(root: Path, param: str, scope: str) -> str:
    result = invoke(
        "orchestra", ["view", "architecture", f"--{param}", scope, "--revision", HEAD], root
    )
    assert result.code == 0, result.err
    return result.out


def _api(project: Project, param: str, scope: str) -> dict:
    client = TestClient(create_app(project), raise_server_exceptions=False)
    response = client.get("/api/architecture", params={param: scope, "revision": HEAD})
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, dict), body
    return body


def _absent(text: str, names: list[str]) -> None:
    for name in names:
        assert name not in text, name


def test_cli_area_scope_shows_its_area_and_hides_the_other(tmp_path: Path) -> None:
    _project(tmp_path)

    out = _cli(tmp_path, "area", "composer")

    for name in (
        "records",
        "Owns records duties.",
        "record-api",
        "typed-records",
        "Typed rows keep reads cheap.",
        "adapters-only",
        "Only adapters touch the store.",
    ):
        assert name in out
    _absent(out, ["views", "view-api", "markdown-views", "paged-views", "views-pure"])


def test_cli_component_scope_shows_its_decisions_and_constraints(tmp_path: Path) -> None:
    _project(tmp_path)

    out = _cli(tmp_path, "component", "records")

    assert "Owns records duties." in out
    assert "record-api" in out
    assert "typed-records" in out
    assert "Typed rows keep reads cheap." in out
    assert "adapters-only" in out
    assert "verified" in out
    assert HEAD in out
    _absent(out, ["views", "view-api", "markdown-views", "views-pure"])


def test_cli_component_scope_marks_proposed_decisions(tmp_path: Path) -> None:
    _project(tmp_path)

    out = _cli(tmp_path, "component", "views")

    proposed = next(line for line in out.splitlines() if "paged-views" in line)
    accepted = next(line for line in out.splitlines() if "markdown-views" in line)
    assert "proposed" in proposed
    assert "proposed" not in accepted
    assert "Paging bounds output." in out
    assert "unverified" in out
    _absent(out, ["records", "typed-records", "shard-records", "adapters-only"])


def test_cli_interface_scope_shows_its_decision_and_connected_component(tmp_path: Path) -> None:
    _project(tmp_path)

    out = _cli(tmp_path, "interface", "record-api")

    assert "Serves record-api callers." in out
    assert "versioned-api" in out
    assert "Clients pin versions." in out
    assert "records" in out
    _absent(out, ["views", "view-api", "typed-records", "markdown-views", "paged-views"])


def test_cli_follows_component_to_decision_rationale_and_constraint(tmp_path: Path) -> None:
    _project(tmp_path)

    out = _cli(tmp_path, "component", "records")

    lines = out.splitlines()
    decision = next(i for i, line in enumerate(lines) if "typed-records" in line)
    rationale = next(i for i, line in enumerate(lines) if "Typed rows keep reads cheap." in line)
    constraint = next(i for i, line in enumerate(lines) if "adapters-only" in line)
    assert decision <= rationale
    assert rationale < constraint
    assert "outcome: verified" in lines[constraint]


def test_api_follows_component_to_decision_rationale_and_constraint(tmp_path: Path) -> None:
    project = _project(tmp_path)

    body = _api(project, "component", "records")

    component = body["areas"][0]["components"][0]
    assert component["name"] == "records"
    decisions = {d["title"]: d for d in component["decisions"]}
    assert "Typed rows keep reads cheap." in str(decisions["typed-records"])
    assert "proposed" in str(decisions["shard-records"])
    constraint = component["constraints"][0]
    assert constraint["name"] == "adapters-only"
    assert constraint["outcome"] == "verified"
    assert constraint["revision"] == HEAD


@pytest.mark.parametrize(("param", "scope"), SCOPES)
def test_api_content_equals_cli_content_for_each_scope(
    tmp_path: Path, param: str, scope: str
) -> None:
    project = _project(tmp_path)

    cli = _cli(tmp_path, param, scope)
    api = _api(project, param, scope)

    assert render_architecture(api).rstrip("\n") == cli.rstrip("\n")
    assert api == architecture_view(project.records(), scope, HEAD)


@pytest.mark.parametrize(("param", "scope"), SCOPES)
def test_api_scope_excludes_items_outside_it(tmp_path: Path, param: str, scope: str) -> None:
    project = _project(tmp_path)

    text = str(_api(project, param, scope))

    in_composer = scope in ("composer", "records", "record-api")
    outside = ["views", "markdown-views"] if in_composer else ["records", "typed-records"]
    _absent(text, outside)
