"""Oracles for the areas view home area rule and for stored effort names."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from dashboard.backend import areas as areas_mod
from dashboard.backend import records as records_mod
from dashboard.backend import snapshot as snapshot_mod
from dashboard.backend.server.app import create_app
from orchestra.canon.project import open_store


def _create(cli, record_type: str, subject: str, payload: dict, body: str | None = None) -> dict:
    args = ["create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)]
    if body is not None:
        args.extend(["--body", body])
    result = cli(*args)
    assert result.returncode == 0, f"create {record_type} {subject}: {result.stdout}"
    return json.loads(result.stdout)["record"]


def _effort(cli, subject: str, **extra: str) -> dict:
    return _create(
        cli, "score:effort", subject, {"goal": f"goal of {subject}", "kind": "deliver", **extra}
    )


def _area(cli, subject: str) -> dict:
    return _create(cli, "composer:area", subject, {"title": subject}, "## Scope\n\nScope.\n")


def _idea(cli, subject: str, **payload: str) -> dict:
    return _create(cli, "composer:idea", subject, payload, f"text of {subject}\n")


def _areas(store: Path) -> dict[str, list[str]]:
    client = TestClient(create_app(open_store(store)), raise_server_exceptions=False)
    response = client.get("/api/areas")
    assert response.status_code == 200, response.text
    return {item["subject"]: [i["subject"] for i in item["ideas"]] for item in response.json()}


def test_areas_view_uses_the_home_area_rule(store, cli, monkeypatch):
    _effort(cli, "alpha")
    _area(cli, "billing")
    _area(cli, "search")
    _create(cli, "composer:placement", "alpha", {"area": "billing"})
    _idea(cli, "refund-flow", status="promoted", effort="alpha")
    assert _areas(store) == {"billing": ["refund-flow"], "search": []}

    monkeypatch.setattr(areas_mod, "home_area", lambda idea, placements: "search", raising=False)
    assert _areas(store) == {"billing": [], "search": ["refund-flow"]}


def test_old_effort_names_are_not_remapped(store, cli):
    _effort(cli, "legacy", status="closed")
    _effort(cli, "renamed")
    _idea(cli, "legacy-idea", status="open", effort="legacy")
    view = snapshot_mod.load_snapshot(open_store(store))
    assert [effort.effort for effort in view.efforts] == ["renamed"]
    assert not hasattr(records_mod, "merge_aliases")
    assert not hasattr(records_mod, "remap_records")
