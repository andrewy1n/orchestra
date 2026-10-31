"""Failure recovery at the Project and backup transaction boundaries."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from orchestra.canon.backend import open_backend
from orchestra.canon.project import Project
from orchestra.canon.sqlite_backend import SqliteBackend
from orchestra.canon.errors import StoreError


@pytest.fixture
def sqlite_project(project: Project) -> Project:
    metadata = open_backend(project.store_path)
    metadata.write_config({**metadata.load_config(), "backend": "sqlite"})
    return project


def _contents(project: Project) -> str:
    with sqlite3.connect(project.store_path / "canon.db") as connection:
        return "\n".join(connection.iterdump())


def test_failed_event_audit_leaves_no_record_or_op(
    sqlite_project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    sqlite_project.create(
        record_type="alpha:task", subject="task", payload={"title": "Task"}
    )
    before = _contents(sqlite_project)

    def reject(self: SqliteBackend, record: dict[str, Any]) -> None:
        raise StoreError("injected audit failure")

    monkeypatch.setattr(SqliteBackend, "archive_history", reject)
    with pytest.raises(StoreError, match="injected audit failure"):
        sqlite_project.create(
            record_type="alpha:log",
            subject="task",
            payload={"task": "task", "message": "Event"},
        )
    assert _contents(sqlite_project) == before
    assert sqlite_project.validate() == []


def test_failed_correction_restores_original_event_and_history(
    sqlite_project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    sqlite_project.create(
        record_type="alpha:task", subject="task", payload={"title": "Task"}
    )
    event = sqlite_project.create(
        record_type="alpha:log",
        subject="task",
        payload={"task": "task", "message": "Event"},
    )
    before = _contents(sqlite_project)

    def reject(self: SqliteBackend, record: dict[str, Any]) -> None:
        raise StoreError("injected audit failure")

    monkeypatch.setattr(SqliteBackend, "archive_history", reject)
    with pytest.raises(StoreError, match="injected audit failure"):
        sqlite_project.correct(event["id"], payload={"message": "Correction"})
    assert _contents(sqlite_project) == before
    assert sqlite_project.get(event["id"]) == event
    assert sqlite_project.validate() == []


def test_nested_write_failure_does_not_poison_outer_transaction(
    sqlite_project: Project,
) -> None:
    backend = open_backend(sqlite_project.store_path)
    record = sqlite_project.create(
        record_type="alpha:task", subject="task", payload={"title": "Task"}
    )
    with backend.transaction():
        with pytest.raises(StoreError, match="already exists"):
            backend.create_record(record)
        changed = backend.write_record(
            {**record, "payload": {"title": "Changed"}},
            expected_revision=record["revision"],
            archive_prior=record,
        )
    assert sqlite_project.get(record["id"]) == changed
    assert sqlite_project.validate() == []


def test_backup_refuses_invalid_retention_and_active_write(
    sqlite_project: Project,
) -> None:
    backend = open_backend(sqlite_project.store_path)
    with pytest.raises(StoreError, match="at least 1"):
        backend.backup(0)
    with backend.transaction(), pytest.raises(StoreError, match="write transaction"):
        backend.backup()
    assert not (sqlite_project.store_path / "backups").exists()


def test_backup_custom_retention(sqlite_project: Project) -> None:
    backend = open_backend(sqlite_project.store_path)
    for _ in range(4):
        backup = Path(backend.backup(keep=2))
        assert backup.is_file()
    assert len(list((sqlite_project.store_path / "backups").glob("*.db"))) == 2
