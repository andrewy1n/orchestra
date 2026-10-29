"""FastAPI write oracles: JSON body, no query string.

Drives ``dashboard.backend.server.app.create_app``. Does not use ``dashboard.backend.server.serve``.
"""

from __future__ import annotations

import sys

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import helpers as h
from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from orchestra.canon.project import open_store  # noqa: E402
from dashboard.backend.server.app import create_app  # noqa: E402


@pytest.fixture()
def defs(resolved_contract):
    return h.record_defs_by_id(resolved_contract)


def _goal(cli, defs) -> None:
    h.create_generic_record(
        cli, defs, "score:effort", subject="alpha",
        extra_payload={"goal": "ship alpha", "kind": "deliver"},
    )


def _client(store) -> TestClient:
    target = open_store(store)
    try:
        app = create_app(target)
    except Exception as exc:
        raise AssertionError(f"create_app failed: {exc}") from exc
    return TestClient(app, raise_server_exceptions=False)


def _snapshot(client: TestClient) -> dict:
    response = client.get("/api/snapshot")
    assert response.status_code == 200, response.text
    return response.json()


def test_r1_backlog_dismiss(store, cli, defs):
    _goal(cli, defs)
    h.create_generic_record(
        cli, defs, "composer:idea", subject="park-me",
        extra_payload={"effort": "alpha", "status": "open", "source": "chat"},
    )
    client = _client(store)
    raw = next(
        item
        for view in _snapshot(client)["efforts"]
        for item in view["backlog"]
        if item["status"] == "open"
    )
    response = client.post(
        "/api/backlog",
        json={"id": raw["id"], "action": "dismiss"},
    )
    assert 200 <= response.status_code < 300, response.text
    remaining = [
        item
        for view in _snapshot(client)["efforts"]
        for item in view["backlog"]
        if item["id"] == raw["id"]
    ]
    assert remaining == []


def test_r2_needs_clear(store, cli, defs):
    _goal(cli, defs)
    h.create_generic_record(
        cli, defs, "score:continuity-question", subject="alpha",
        extra_payload={"blocking": True, "scope": "which backend"},
    )
    client = _client(store)
    raw = next(
        item
        for view in _snapshot(client)["efforts"]
        for item in view["needs_you"]
        if item["kind"] == "blocking-question"
    )
    response = client.post(
        "/api/needs",
        json={"id": raw["id"], "action": "approve", "revision": raw["revision"]},
    )
    assert 200 <= response.status_code < 300, response.text
    remaining = [
        item
        for view in _snapshot(client)["efforts"]
        for item in view["needs_you"]
        if item["id"] == raw["id"]
    ]
    assert remaining == []


def test_r3_openapi(store):
    client = _client(store)
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
