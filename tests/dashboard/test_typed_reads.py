from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from dashboard_seed_support import seed_project
from fastapi.testclient import TestClient

from dashboard.backend import records, store
from dashboard.backend.server.app import create_app
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project


@pytest.fixture()
def project(tmp_path: Path) -> Project:
    return seed_project(tmp_path)


@pytest.fixture()
def failing_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(store, "_catalog_cache", {})

    def fail(_project: Project) -> list[object]:
        raise StoreError("store unreadable")

    monkeypatch.setattr(Project, "records", fail)


def _ids(project: Project) -> dict[str, str]:
    return {
        "idea": project.list("composer:idea")[0]["id"],
        "question": project.list("score:continuity-question")[0]["id"],
        "task": project.list("score:work-item")[0]["id"],
    }


SOFT_TYPES = [
    "score:specification",
    "score:design",
    "conductor:assessment",
    "conductor:integration-report",
    "conductor:proof-packet",
    "conductor:release",
    "score:position",
    "composer:idea",
    "score:milestone",
    "composer:area",
]

ROUTES: list[Callable[[dict[str, str]], str]] = [
    lambda _ids: "/api/snapshot",
    lambda _ids: "/api/hub",
    lambda _ids: "/api/areas",
    lambda _ids: "/api/phase?effort=e&phase=p",
    lambda ids: f"/api/task?id={ids['task']}",
    lambda _ids: "/api/journal?effort=e",
    lambda ids: f"/api/record?id={ids['task']}",
    lambda _ids: "/api/requirement?effort=e&phase=p&id=R1",
    lambda ids: f"/api/needs?effort=e&id={ids['question']}",
    lambda ids: f"/api/backlog?effort=e&id={ids['idea']}",
]
ROUTE_NAMES = [
    "snapshot",
    "hub",
    "areas",
    "phase",
    "task",
    "journal",
    "record",
    "requirement",
    "needs",
    "backlog",
]


@pytest.mark.parametrize("route", ROUTES, ids=ROUTE_NAMES)
def test_http_required_read_fails_with_error_body(
    project: Project, failing_reads: None, route: Callable[[dict[str, str]], str]
) -> None:
    ids = _ids(project)
    client = TestClient(create_app(project), raise_server_exceptions=False)
    response = client.get(route(ids))
    assert response.status_code == 404, response.text
    assert "catalog read failed" in response.json()["error"]


def test_list_records_required_read_fails_raises_model_error(
    project: Project, failing_reads: None
) -> None:
    with pytest.raises(store.ModelError, match="failed"):
        store.list_records(project, "score:effort")


def test_list_records_required_read_fails_for_untyped_listing(
    project: Project, failing_reads: None
) -> None:
    with pytest.raises(store.ModelError, match="failed"):
        store.list_records(project, subject="e")


def test_get_record_required_read_fails_raises_model_error(
    project: Project, failing_reads: None
) -> None:
    with pytest.raises(store.ModelError, match="catalog read failed"):
        store.get_record(project, _ids(project)["task"])


def test_catalog_records_required_read_fails_raises_model_error(
    project: Project, failing_reads: None
) -> None:
    with pytest.raises(store.ModelError, match="catalog read failed"):
        store.catalog_records(project)


def test_soft_record_types_required_read_fails_raises_model_error(
    project: Project, failing_reads: None
) -> None:
    for record_type in SOFT_TYPES:
        with pytest.raises(store.ModelError):
            records.list_records(project, record_type)
