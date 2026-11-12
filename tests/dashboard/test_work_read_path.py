from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import pytest
from canon_support import make_project
from fastapi.testclient import TestClient

from dashboard.backend.hub import build_hub
from dashboard.backend.server import service
from dashboard.backend.server.app import create_app
from dashboard.backend.snapshot import load_snapshot, load_work_snapshot
from orchestra.canon.project import Project
from orchestra.canon.sqlite_backend import SqliteBackend
from orchestra.canon.types import JsonObject, Record

NOW = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
BODY = (
    "## Problem\n\nP\n\n## Approach\n\nA\n\n## Exit criteria\n\nE\n\n"
    "## Requirements\n\nR1: Behavior.\n\n## Run facts\n\nretry_max_fix_tasks: 7\n"
)


def _create(
    project: Project, kind: str, subject: str, payload: JsonObject, body: str | None = None
) -> Record:
    if body is None:
        body = "\n\n".join(f"## {name}\n\nText." for name in project.schemas().types[kind].sections)
    return project.create(record_type=kind, subject=subject, payload=payload, body=body)


@pytest.fixture()
def project(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    _create(project, "score:effort", "e", {"goal": "Ship", "kind": "deliver"})
    for ordinal, name in enumerate(("p", "past"), 1):
        phase = _create(
            project,
            "score:phase",
            name,
            {"title": name, "ordinal": ordinal, "effort": "e", "weight": "light"},
            BODY,
        )
        phase = project.update(phase["id"], transition="in_progress")
        if name == "past":
            project.update(phase["id"], transition="done")
    task_inputs: tuple[tuple[str, str, tuple[str, ...], JsonObject], ...] = (
        ("done", "p", ("in_progress", "done"), {}),
        ("fix-running", "p", ("in_progress",), {"attempts": 2, "depends_on": ["done"]}),
        ("future", "p", (), {"depends_on": ["fix-running"]}),
        ("withdrawn", "p", ("withdrawn",), {}),
        ("old-task", "past", ("in_progress", "done"), {}),
    )
    for name, phase, states, extra in task_inputs:
        task = _create(
            project,
            "score:work-item",
            name,
            {
                "title": name,
                "effort": "e",
                "phase": phase,
                "kind": "repair",
                "assignee": "",
                **extra,
            },
        )
        for state in states:
            task = project.update(task["id"], transition=state)
    acceptance = _create(
        project,
        "score:acceptance",
        "done",
        {
            "effort": "e",
            "phase": "p",
            "method": "check",
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    _create(
        project,
        "tuner:check-run",
        "done",
        {
            "effort": "e",
            "criterion_id": acceptance["id"],
            "revision": "abc",
            "result": "pass",
            "method": "check",
            "signed_by": "",
        },
    )
    _create(project, "composer:idea", "idea", {"effort": "e", "status": "open"})
    _create(
        project,
        "score:continuity-question",
        "e",
        {"owner": "user", "blocking": True, "scope": "plan"},
    )
    return project


@pytest.mark.parametrize(
    "path",
    [
        "/api/token",
        "/api/hub",
        "/api/snapshot",
        "/api/areas",
        "/api/phase?effort=e&phase=p",
        "/api/journal?effort=e",
        "/api/requirement?effort=e&phase=p&id=R1",
    ],
)
def test_reader_get_requests_do_not_initialize_sqlite(
    project: Project, monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    def forbid(_backend: SqliteBackend) -> None:
        raise AssertionError("Reader initializes SQLite")

    monkeypatch.setattr(SqliteBackend, "_initialize_database", forbid)
    response = TestClient(create_app(project)).get(path)
    assert response.status_code == 200, response.text


def test_work_card_input_reads_do_not_initialize_sqlite(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = service.Reader(project)
    snapshot = load_work_snapshot(project, NOW)

    def forbid(_backend: SqliteBackend) -> None:
        raise AssertionError("Progress card reads initialize SQLite")

    monkeypatch.setattr(SqliteBackend, "_initialize_database", forbid)
    _landings, approvals, _reviews = reader._card_inputs(snapshot)
    assert "p" in approvals


def test_direct_compact_work_read_does_not_initialize_sqlite(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbid(_backend: SqliteBackend) -> None:
        raise AssertionError("Compact Work initializes SQLite")

    monkeypatch.setattr(SqliteBackend, "_initialize_database", forbid)
    snapshot = load_work_snapshot(project, NOW)
    assert [phase.subject for effort in snapshot.efforts for phase in effort.phases] == ["p"]


def test_compact_work_preserves_full_progress_cards(project: Project) -> None:
    full = build_hub(load_snapshot(project, NOW), NOW)
    compact = build_hub(load_work_snapshot(project, NOW), NOW)
    assert compact == full
    progress = compact.active_phases[0].progress
    assert progress is not None
    assert (
        progress.tasks.done,
        progress.tasks.running,
        progress.tasks.remaining,
        progress.tasks.wave,
    ) == (1, 1, 1, 2)
    assert progress.repairs is not None
    assert (progress.repairs.used, progress.repairs.limit) == (1, 7)
    assert all(item.kind != "phase" for item in compact.work_next)


def test_reader_keeps_ui_write_actions_writable(project: Project) -> None:
    reader = service.Reader(project)
    idea = project.resolve("composer:idea", "idea")
    assert reader.target is project
    assert reader.write_backlog({"effort": "e", "id": idea["id"], "action": "dismiss"}).ok
    assert project.resolve("composer:idea", "idea")["payload"].get("status") == "dismissed"


@pytest.mark.parametrize("operation", ["token", "hub"])
def test_work_reads_complete_while_a_writer_holds_a_transaction(
    project: Project, operation: str
) -> None:
    writer = SqliteBackend(project.store_path, project.store_path)
    reader = service.Reader(project)
    finished = threading.Event()

    def read() -> object:
        result = reader.token() if operation == "token" else reader.hub()
        finished.set()
        return result

    with ThreadPoolExecutor(max_workers=1) as pool:
        with writer.transaction():
            pending = pool.submit(read)
            assert finished.wait(3), "Reader waits for a writer transaction"
        assert pending.result(timeout=10) is not None


def test_work_card_inputs_reuse_the_pinned_catalog(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = service.Reader(project)
    snapshot = load_work_snapshot(project, NOW)
    original = service.store.catalog_records
    calls = 0

    def catalog(target: Project) -> list[Record]:
        nonlocal calls
        calls += 1
        assert target.read_only
        return original(target)

    def forbid(*_args: object) -> None:
        raise AssertionError("Progress cards repeat catalog discovery")

    monkeypatch.setattr(service.store, "catalog_records", catalog)
    monkeypatch.setattr(service.store, "change_token", forbid)
    monkeypatch.setattr(Project, "schemas", forbid)
    reader._card_inputs(snapshot)
    assert calls == 1
