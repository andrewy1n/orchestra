"""Oracles for promoted ideas listed under the area their effort is placed in."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from orchestra.canon.project import open_store  # noqa: E402
from dashboard.backend.server.app import create_app  # noqa: E402


def _create(cli, record_type: str, subject: str, payload: dict, body: str | None = None) -> dict:
    args = ["create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)]
    if body is not None:
        args.extend(["--body", body])
    result = cli(*args)
    assert result.returncode == 0, (
        f"create {record_type} {subject}: {result.stdout}\n{result.stderr}"
    )
    return json.loads(result.stdout)["record"]


def _effort(cli, subject: str) -> dict:
    return _create(cli, "score:effort", subject, {"goal": f"goal of {subject}", "kind": "deliver"})


def _area(cli, subject: str, title: str, scope: str) -> dict:
    return _create(cli, "composer:area", subject, {"title": title}, f"## Scope\n\n{scope}\n")


def _place(cli, effort: str, area: str) -> dict:
    return _create(cli, "composer:placement", effort, {"area": area})


def _idea(cli, subject: str, status: str = "open", text: str | None = None, **refs: str) -> dict:
    return _create(
        cli,
        "composer:idea",
        subject,
        {"status": status, **refs},
        f"{text or 'text of ' + subject}\n",
    )


def _areas(store: Path) -> dict[str, dict]:
    client = TestClient(create_app(open_store(store)), raise_server_exceptions=False)
    response = client.get("/api/areas")
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, list), body
    return {item["subject"]: item for item in body}


def _idea_subjects(area: dict) -> list[str]:
    return sorted(idea["subject"] for idea in area["ideas"])


def test_r14_promoted_idea_shows_in_the_area_its_effort_is_placed_in(store, cli):
    _effort(cli, "alpha")
    _area(cli, "billing", "Billing", "Invoices.")
    _place(cli, "alpha", "billing")
    _idea(cli, "refund-flow", status="promoted", effort="alpha")
    ideas = {idea["subject"]: idea for idea in _areas(store)["billing"]["ideas"]}
    assert list(ideas) == ["refund-flow"]
    assert ideas["refund-flow"]["status"] == "promoted"
    assert ideas["refund-flow"]["effort"] == "alpha"


def test_r14_promoted_idea_does_not_show_in_an_area_its_effort_is_not_placed_in(store, cli):
    _effort(cli, "alpha")
    _area(cli, "billing", "Billing", "Invoices.")
    _area(cli, "search", "Search", "Ranking.")
    _place(cli, "alpha", "billing")
    _idea(cli, "refund-flow", status="promoted", effort="alpha")
    areas = _areas(store)
    assert _idea_subjects(areas["billing"]) == ["refund-flow"]
    assert _idea_subjects(areas["search"]) == []


def test_r14_promoted_idea_shows_in_the_placed_area_when_the_idea_names_no_area(store, cli):
    _effort(cli, "alpha")
    _area(cli, "billing", "Billing", "Invoices.")
    _place(cli, "alpha", "billing")
    _idea(cli, "unfiled", status="promoted", effort="alpha")
    areas = _areas(store)
    assert _idea_subjects(areas["billing"]) == ["unfiled"]
    assert not {i["subject"]: i for i in areas["billing"]["ideas"]}["unfiled"]["area"]
