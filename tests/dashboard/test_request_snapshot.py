from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from dashboard_seed_support import seed_project
from fastapi.testclient import TestClient

from dashboard.backend import store
from dashboard.backend.server import service
from dashboard.backend.server.app import create_app
from dashboard.backend.snapshot import Snapshot
from orchestra.canon.project import Project
from orchestra.conductor.attention import LandingFact


@dataclass
class Counts:
    catalog_loads: int = 0
    snapshot_builds: list[str] = field(default_factory=list)
    change_tokens: int = 0

    def reset(self) -> None:
        self.catalog_loads = 0
        self.snapshot_builds.clear()
        self.change_tokens = 0


@pytest.fixture()
def project(tmp_path: Path) -> Project:
    return seed_project(tmp_path)


@pytest.fixture()
def counts(monkeypatch: pytest.MonkeyPatch) -> Counts:
    monkeypatch.setattr(store, "_catalog_cache", {})
    seen = Counts()
    load_catalog = store.load_catalog
    change_token = Project.change_token
    load_snapshot = service.load_snapshot
    load_work_snapshot = service.load_work_snapshot

    def counted_catalog(target: Project, token: str) -> store.Catalog:
        seen.catalog_loads += 1
        return load_catalog(target, token)

    def counted_token(target: Project) -> str:
        seen.change_tokens += 1
        return change_token(target)

    def counted_snapshot(target: Project, *args: object, **kwargs: object) -> Snapshot:
        seen.snapshot_builds.append("full")
        return load_snapshot(target, *args, **kwargs)  # pyright: ignore[reportArgumentType]

    def counted_work_snapshot(target: Project, *args: object, **kwargs: object) -> Snapshot:
        seen.snapshot_builds.append("work")
        return load_work_snapshot(target, *args, **kwargs)  # pyright: ignore[reportArgumentType]

    monkeypatch.setattr(store, "load_catalog", counted_catalog)
    monkeypatch.setattr(Project, "change_token", counted_token)
    monkeypatch.setattr(service, "load_snapshot", counted_snapshot)
    monkeypatch.setattr(service, "load_work_snapshot", counted_work_snapshot)
    return seen


def _ids(project: Project) -> dict[str, str]:
    return {
        "idea": project.list("composer:idea")[0]["id"],
        "question": project.list("score:continuity-question")[0]["id"],
        "task": project.list("score:work-item")[0]["id"],
    }


ROUTES: dict[str, Callable[[dict[str, str]], str]] = {
    "snapshot": lambda _ids: "/api/snapshot",
    "hub": lambda _ids: "/api/hub",
    "areas": lambda _ids: "/api/areas",
    "phase": lambda _ids: "/api/phase?effort=e&phase=p",
    "task": lambda ids: f"/api/task?id={ids['task']}",
    "journal": lambda _ids: "/api/journal?effort=e",
    "record": lambda ids: f"/api/record?id={ids['task']}",
    "requirement": lambda _ids: "/api/requirement?effort=e&phase=p&id=R1",
    "needs": lambda ids: f"/api/needs?effort=e&id={ids['question']}",
    "backlog": lambda ids: f"/api/backlog?effort=e&id={ids['idea']}",
}
SNAPSHOT_ROUTES = ("snapshot", "hub", "needs", "backlog")


def _get(project: Project, counts: Counts, name: str) -> None:
    ids = _ids(project)
    client = TestClient(create_app(project), raise_server_exceptions=False)
    counts.reset()
    response = client.get(ROUTES[name](ids))
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("name", SNAPSHOT_ROUTES)
def test_one_snapshot_is_built_for_each_request(
    project: Project, counts: Counts, name: str
) -> None:
    _get(project, counts, name)
    assert len(counts.snapshot_builds) == 1


@pytest.mark.parametrize("name", SNAPSHOT_ROUTES)
def test_one_snapshot_serves_the_request_catalog(
    project: Project, counts: Counts, name: str
) -> None:
    _get(project, counts, name)
    assert counts.catalog_loads == 1


@pytest.mark.parametrize("name", sorted(ROUTES))
def test_routes_reuse_one_catalog_load_per_request(
    project: Project, counts: Counts, name: str
) -> None:
    _get(project, counts, name)
    assert counts.catalog_loads == 1


@pytest.mark.parametrize("name", sorted(ROUTES))
def test_routes_reuse_one_pinned_change_token_per_request(
    project: Project, counts: Counts, name: str
) -> None:
    _get(project, counts, name)
    assert counts.change_tokens == 1


@pytest.mark.parametrize("name", SNAPSHOT_ROUTES)
def test_one_snapshot_is_built_for_each_request_with_landing_facts(
    project: Project, counts: Counts, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    facts = {"p": LandingFact(exists=True, merged=False, branch="phase/p", ahead=1)}
    monkeypatch.setattr(service, "landing_facts", lambda _view, _root: facts)
    _get(project, counts, name)
    assert len(counts.snapshot_builds) == 1
    assert counts.catalog_loads == 1
