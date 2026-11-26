"""Oracles for the architecture view the dashboard backend returns."""

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
from dashboard.backend.architecture import load_architecture
from dashboard.backend.server.app import create_app
from orchestra.canon.project import Project
from orchestra.views.architecture import architecture_view, render_architecture

HEAD = "a" * 40


def _project(root: Path) -> Project:
    project = make_project(root)
    project.create(
        record_type="composer:component",
        subject="records",
        payload={"area": "composer"},
        body="## Responsibility\nOwns record data.\n",
    )
    project.create(
        record_type="composer:component",
        subject="views",
        payload={"area": "interfaces"},
        body="## Responsibility\nRenders views.\n",
    )
    project.create(
        record_type="composer:interface",
        subject="record-api",
        payload={"connects": ["records"]},
        body="## Provides\nServes record callers.\n",
    )
    project.create(
        record_type="composer:architecture-decision",
        subject="typed-records",
        payload={"status": "accepted", "affects": ["records", "record-api"]},
        body="## Rationale\nKeeps reads cheap.\n",
    )
    project.create(
        record_type="score:standing-constraint",
        subject="adapters-only",
        payload={
            "area": "composer",
            "rule": "Only adapters touch the store.",
            "check": "scripts/check-adapters",
            "targets": ["records"],
        },
        body="## Basis\nIsolation.\n",
    )
    return project


def _get(project: Project, **params: str):
    client = TestClient(create_app(project), raise_server_exceptions=False)
    return client.get("/api/architecture", params={"revision": HEAD, **params})


def _body(project: Project, **params: str) -> dict:
    response = _get(project, **params)
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, dict), body
    return body


def test_r11_full_view_lists_areas_components_and_interfaces(tmp_path):
    body = _body(_project(tmp_path))
    assert body["revision"] == HEAD
    assert [a["name"] for a in body["areas"]] == ["composer", "interfaces"]
    assert [c["name"] for c in body["areas"][0]["components"]] == ["records"]
    assert [i["name"] for i in body["interfaces"]] == ["record-api"]


def test_r11_endpoint_json_equals_architecture_view_for_the_full_query(tmp_path):
    project = _project(tmp_path)
    assert _body(project) == architecture_view(project.records(), None, HEAD)


@pytest.mark.parametrize(
    ("param", "scope"),
    [("area", "composer"), ("component", "records"), ("interface", "record-api")],
)
def test_r11_endpoint_json_equals_architecture_view_for_each_scope(tmp_path, param, scope):
    project = _project(tmp_path)
    assert _body(project, **{param: scope}) == architecture_view(project.records(), scope, HEAD)


def test_r11_endpoint_content_renders_to_the_cli_text(tmp_path):
    project = _project(tmp_path)
    cli = invoke("orchestra", ["view", "architecture", "--revision", HEAD], tmp_path)
    assert cli.code == 0, cli.err
    assert render_architecture(_body(project)).rstrip("\n") == cli.out.rstrip("\n")


def test_r11_scoped_endpoint_content_renders_to_the_cli_text(tmp_path):
    project = _project(tmp_path)
    cli = invoke(
        "orchestra",
        ["view", "architecture", "--component", "records", "--revision", HEAD],
        tmp_path,
    )
    assert cli.code == 0, cli.err
    assert render_architecture(_body(project, component="records")).rstrip("\n") == (
        cli.out.rstrip("\n")
    )


def test_r11_revision_reaches_the_constraint_outcome(tmp_path):
    body = _body(_project(tmp_path), component="records")
    constraint = body["areas"][0]["components"][0]["constraints"][0]
    assert constraint["name"] == "adapters-only"
    assert constraint["outcome"] == "unverified"
    assert constraint["revision"] == HEAD


def test_r11_unknown_scope_fails_with_an_error_body(tmp_path):
    response = _get(_project(tmp_path), component="nope")
    assert response.status_code == 404
    assert "nope" in response.json()["error"]


def test_r11_more_than_one_scope_is_rejected(tmp_path):
    response = _get(_project(tmp_path), area="composer", component="records")
    assert response.status_code == 400


def test_r11_load_architecture_returns_the_shared_view(tmp_path):
    project = _project(tmp_path)
    assert load_architecture(project, "records", HEAD) == architecture_view(
        project.records(), "records", HEAD
    )
