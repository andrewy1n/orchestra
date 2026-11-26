"""Oracles for the product overview the dashboard backend returns."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from conftest import REPO_ROOT
from fastapi.testclient import TestClient

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend.product import load_product
from dashboard.backend.server.app import create_app
from orchestra.canon.project import open_store


def _create(cli, record_type: str, subject: str, payload: dict) -> dict:
    result = cli(
        "create",
        "--type",
        record_type,
        "--subject",
        subject,
        "--payload",
        json.dumps(payload),
    )
    assert result.returncode == 0, (
        f"create {record_type} {subject}: {result.stdout}\n{result.stderr}"
    )
    return json.loads(result.stdout)["record"]


def _statement(cli, purpose: str, audience: str) -> dict:
    return _create(cli, "composer:product", "product", {"purpose": purpose, "audience": audience})


def _item(cli, subject: str, title: str, description: str, status: str) -> dict:
    return _create(
        cli,
        "composer:product-item",
        subject,
        {"title": title, "description": description, "status": status},
    )


def _product(store: Path) -> dict:
    response = TestClient(create_app(open_store(store)), raise_server_exceptions=False).get(
        "/api/product"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, dict), body
    return body


def test_r7_overview_lists_statement_first_then_capabilities_and_goals(store, cli):
    _statement(cli, "Keep work verifiable.", "Teams shipping with agents.")
    _item(cli, "live-roadmap", "Live roadmap", "Shows work as it stands.", "current")
    _item(cli, "export", "Export", "Share the roadmap as a file.", "planned")
    body = _product(store)
    assert list(body)[0] == "statement"
    assert body["statement"]["purpose"] == "Keep work verifiable."
    assert body["statement"]["audience"] == "Teams shipping with agents."
    assert [item["subject"] for item in body["capabilities"]] == ["live-roadmap"]
    assert [item["subject"] for item in body["goals"]] == ["export"]


def test_r7_capabilities_and_goals_carry_title_description_and_status(store, cli):
    _statement(cli, "Purpose.", "Audience.")
    _item(cli, "live-roadmap", "Live roadmap", "Shows work as it stands.", "current")
    _item(cli, "export", "Export", "Share the roadmap as a file.", "planned")
    body = _product(store)
    capability = body["capabilities"][0]
    assert capability["title"] == "Live roadmap"
    assert capability["description"] == "Shows work as it stands."
    assert capability["status"] == "current"
    goal = body["goals"][0]
    assert goal["title"] == "Export"
    assert goal["description"] == "Share the roadmap as a file."
    assert goal["status"] == "planned"


def test_r7_a_superseded_item_never_shows(store, cli):
    _statement(cli, "Purpose.", "Audience.")
    record = _item(cli, "export", "Export", "Share the roadmap as a file.", "planned")
    result = cli(
        "supersede",
        "--type",
        record["record_type"],
        "--id",
        record["id"],
        "--expected-revision",
        "@current",
        "--payload",
        json.dumps(
            {"title": "Export", "description": "Share it as a file.", "status": "current"}
        ),
    )
    assert result.returncode == 0, result.stderr
    body = _product(store)
    assert body["goals"] == []
    assert [item["description"] for item in body["capabilities"]] == ["Share it as a file."]


def test_r7_no_statement_gives_an_explicit_empty_result(store, cli):
    _item(cli, "live-roadmap", "Live roadmap", "Shows work as it stands.", "current")
    body = _product(store)
    assert "statement" in body
    assert body["statement"] is None
    assert [item["subject"] for item in body["capabilities"]] == ["live-roadmap"]


def test_r7_an_empty_store_returns_no_statement_capabilities_or_goals(store, cli):
    assert _product(store) == {"statement": None, "capabilities": [], "goals": []}


def test_r7_load_product_returns_the_record_text_unchanged(store, cli):
    _statement(cli, "Keep work verifiable.", "Teams shipping with agents.")
    _item(cli, "live-roadmap", "Live roadmap", "Shows work as it stands.", "current")
    overview = load_product(open_store(store))
    assert overview.statement is not None
    assert overview.statement.purpose == "Keep work verifiable."
    assert [(e.title, e.description, e.status) for e in overview.capabilities] == [
        ("Live roadmap", "Shows work as it stands.", "current")
    ]
