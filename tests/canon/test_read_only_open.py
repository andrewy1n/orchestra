from __future__ import annotations

import multiprocessing
import sqlite3
from pathlib import Path

import pytest
from conftest import make_task

from orchestra.canon.errors import ReadOnlyStoreError, StoreError, StoreNotInitializedError
from orchestra.canon.project import NoArtifactStoreError, Project, open_store


@pytest.fixture
def seeded(project: Project, repo: Path) -> Project:
    first = make_task(project, "first")
    project.update(first["id"], transition="in_progress")
    make_task(project, "second", owner="ann")
    return project


@pytest.fixture
def reader(seeded: Project, repo: Path) -> Project:
    return open_store(repo, read_only=True)


def _db(project: Project) -> Path:
    return project.store_path / "canon.db"


def _tables(db: Path) -> set[str]:
    with sqlite3.connect(db) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}


def test_r6_read_only_open_returns_a_read_only_project(seeded: Project, repo: Path) -> None:
    reader = open_store(repo, read_only=True)
    assert reader.read_only is True
    assert reader.store_path == seeded.store_path
    assert open_store(repo).read_only is False
    assert seeded.read_only is False


def test_r6_read_only_open_by_explicit_store_and_env(
    seeded: Project, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert open_store(repo, store=seeded.store_path, read_only=True).read_only is True
    monkeypatch.setenv("CANON_STORE", str(seeded.store_path))
    assert open_store(repo, read_only=True).read_only is True


def test_r7_every_write_method_raises_read_only_error(reader: Project, seeded: Project) -> None:
    record = seeded.resolve("task", "first")
    before = (_db(seeded).read_bytes(), seeded.change_token())
    operation = {"op": "create", "type": "alpha:task", "subject": "x", "payload": {"title": "x"}}
    writes = {
        "create": lambda: reader.create(
            record_type="alpha:task", subject="x", payload={"title": "x"}
        ),
        "update": lambda: reader.update(record["id"], payload={"owner": "bob"}),
        "supersede": lambda: reader.supersede(record["id"]),
        "correct": lambda: reader.correct(record["id"], payload={"owner": "bob"}),
        "apply": lambda: reader.apply([operation]),
        "apply_at_snapshot": lambda: reader.apply_at_snapshot([operation], reader.change_token()),
    }
    for call in writes.values():
        with pytest.raises(ReadOnlyStoreError):
            call()
    assert issubclass(ReadOnlyStoreError, StoreError)
    assert (_db(seeded).read_bytes(), seeded.change_token()) == before
    assert reader.get(record["id"]) == record


def test_r8_reads_match_a_normal_open(reader: Project, seeded: Project) -> None:
    record = seeded.resolve("task", "first")
    assert reader.get(record["id"]) == seeded.get(record["id"])
    assert reader.get(record["id"], "task") == seeded.get(record["id"], "task")
    assert reader.list("alpha:task") == seeded.list("alpha:task")
    assert reader.records() == seeded.records()
    assert reader.resolve("task", "second") == seeded.resolve("task", "second")
    assert reader.derived() == seeded.derived()
    assert reader.validate() == seeded.validate() == []
    assert reader.config() == seeded.config()
    assert reader.change_token() == seeded.change_token()
    assert set(reader.schemas().types) == set(seeded.schemas().types)


def test_r8_reading_changes_nothing_on_disk(reader: Project, seeded: Project) -> None:
    db = _db(seeded)
    before, tables = db.read_bytes(), _tables(db)
    reader.records()
    reader.validate()
    reader.change_token()
    assert db.read_bytes() == before
    assert _tables(db) == tables


def test_r8_read_only_project_sees_later_writes(reader: Project, seeded: Project) -> None:
    token = reader.change_token()
    make_task(seeded, "third")
    assert reader.change_token() != token
    assert {r["subject"] for r in reader.list("alpha:task")} == {"first", "second", "third"}


def test_r9_missing_database_raises_and_creates_none(seeded: Project, repo: Path) -> None:
    store = seeded.store_path
    for leftover in store.glob("canon.db*"):
        leftover.unlink()
    with pytest.raises(StoreNotInitializedError, match="no database file"):
        open_store(repo, read_only=True)
    with pytest.raises(StoreNotInitializedError):
        open_store(repo, store=store, read_only=True)
    assert list(store.glob("canon.db*")) == []


def test_r9_missing_global_data_root_is_not_created(
    seeded: Project, repo: Path, tmp_path: Path
) -> None:
    (seeded.store_path / "store-binding.local.json").write_text('{"store":"global"}')
    for leftover in seeded.store_path.glob("canon.db*"):
        leftover.unlink()
    with pytest.raises(StoreNotInitializedError):
        open_store(repo, read_only=True)
    assert not (tmp_path / "conftest-home" / ".canon").exists()


def test_r9_read_only_open_without_a_store_fails_as_a_normal_open(repo: Path) -> None:
    with pytest.raises(NoArtifactStoreError):
        open_store(repo, read_only=True)


def _write_tasks(repo: str, count: int, started) -> None:
    writer = open_store(repo)
    for index in range(count):
        make_task(writer, f"concurrent-{index}")
        started.set()


def test_r10_read_only_project_reads_during_concurrent_write(seeded: Project, repo: Path) -> None:
    reader = open_store(repo, read_only=True)
    count, base = 25, len(reader.list("alpha:task"))
    context = multiprocessing.get_context("spawn")
    started = context.Event()
    process = context.Process(target=_write_tasks, args=(str(repo), count, started))
    process.start()
    try:
        assert started.wait(timeout=30)
        seen = [len(reader.list("alpha:task"))]
        while process.is_alive():
            seen.append(len(reader.list("alpha:task")))
        process.join(timeout=30)
        assert process.exitcode == 0
    finally:
        if process.is_alive():
            process.terminate()
    assert seen == sorted(seen)
    assert seen[0] >= base
    assert len(reader.list("alpha:task")) == base + count
    assert reader.validate() == []
