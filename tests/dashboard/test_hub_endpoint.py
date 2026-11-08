"""Oracles for the read-only hub endpoint of the web dashboard."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from conftest import REPO_ROOT
from fastapi.testclient import TestClient

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend.server.app import create_app
from orchestra.canon.project import open_store

HUB_KEYS = {"work_next", "needs_you", "active_phases", "open_ideas", "generated_at"}


def _create(cli, record_type: str, subject: str, payload: dict, body: str | None = None) -> dict:
    args = ["create", "--type", record_type, "--subject", subject, "--payload", json.dumps(payload)]
    if body is not None:
        args.extend(["--body", body])
    result = cli(*args)
    assert result.returncode == 0, (
        f"create {record_type} {subject}: {result.stdout}\n{result.stderr}"
    )
    return json.loads(result.stdout)["record"]


def _open_idea(cli) -> None:
    _create(cli, "score:effort", "alpha", {"goal": "ship alpha", "kind": "deliver"})
    _create(
        cli,
        "composer:idea",
        "an-idea",
        {"effort": "alpha", "status": "open", "source": "chat"},
        "text of an-idea\n",
    )


def _client(store: Path) -> TestClient:
    return TestClient(create_app(open_store(store)), raise_server_exceptions=False)


def _digest(store: Path) -> dict[str, str]:
    return {
        str(path.relative_to(store)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(store.rglob("*"))
        if path.is_file() and ".git" not in path.relative_to(store).parts
    }


def test_r11_get_hub_returns_the_typed_shape(store, cli):
    _open_idea(cli)
    response = _client(store).get("/api/hub")
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == HUB_KEYS
    for key in HUB_KEYS - {"generated_at"}:
        assert isinstance(body[key], list), body
    assert isinstance(body["generated_at"], str)


def test_r11_get_hub_lists_an_open_idea_with_a_title(store, cli):
    _open_idea(cli)
    body = _client(store).get("/api/hub").json()
    assert body["open_ideas"], body
    assert all(isinstance(item, dict) and "title" in item for item in body["open_ideas"])


def test_r11_post_to_hub_is_rejected_with_405(store):
    response = _client(store).post("/api/hub", json={})
    assert response.status_code == 405, response.text


def test_r11_put_and_delete_to_hub_are_rejected_with_405(store):
    client = _client(store)
    assert client.put("/api/hub", json={}).status_code == 405
    assert client.delete("/api/hub").status_code == 405


def test_r11_get_hub_leaves_store_records_unchanged(store, cli):
    _open_idea(cli)
    before = _digest(store)
    response = _client(store).get("/api/hub")
    assert response.status_code == 200, response.text
    assert _digest(store) == before
