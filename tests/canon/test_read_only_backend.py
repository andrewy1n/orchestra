from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Callable
from pathlib import Path

import pytest

from orchestra.canon.config import new_config
from orchestra.canon.errors import ReadOnlyStoreError, StoreError, StoreNotInitializedError
from orchestra.canon.sqlite_backend import SqliteBackend
from orchestra.canon.types import Record


def _record(label: str) -> Record:
    return {
        "id": f"rec-{uuid.uuid5(uuid.NAMESPACE_URL, label)}",
        "record_type": "contract:setting",
        "subject": label,
        "payload": {"title": label},
        "lifecycle_state": "active",
        "relationships": {},
        "recorded_at": "2026-01-01T00:00:00+00:00",
        "body": "",
        "revision": "sha256:pending",
    }


@pytest.fixture
def roots(tmp_path: Path) -> tuple[Path, Path]:
    config_root, data_root = tmp_path / "meta", tmp_path / "data"
    writer = SqliteBackend(config_root, data_root)
    writer.init(new_config({"contract": "0.1.0"}), {})
    writer.create_record(_record("first"))
    return config_root, data_root


def _reader(roots: tuple[Path, Path]) -> SqliteBackend:
    return SqliteBackend(roots[0], roots[1], read_only=True)


def _tables(db: Path) -> set[str]:
    with sqlite3.connect(db) as connection:
        return {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}


def test_r1_connection_rejects_writes(roots: tuple[Path, Path]) -> None:
    connection = _reader(roots)._connect()
    try:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("CREATE TABLE intruder(a)")
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("DELETE FROM records")
        assert connection.execute("SELECT COUNT(*) FROM records").fetchone() == (1,)
    finally:
        connection.close()


def test_r2_mutating_methods_raise_read_only_error(roots: tuple[Path, Path]) -> None:
    reader = _reader(roots)
    record = _record("second")
    calls: dict[str, Callable[[], object]] = {
        "transaction": lambda: reader.transaction().__enter__(),
        "write_config": lambda: reader.write_config(new_config({"contract": "0.1.0"})),
        "write_snapshot": lambda: reader.write_snapshot("contract", "{}"),
        "init": lambda: reader.init(new_config({"contract": "0.1.0"}), {}),
        "backup": lambda: reader.backup(),
        "create_record": lambda: reader.create_record(record),
        "write_record": lambda: reader.write_record(record, expected_revision="x"),
        "delete_record": lambda: reader.delete_record(record["record_type"], record["id"]),
        "archive_history": lambda: reader.archive_history(record),
        "import_record": lambda: reader.import_record(record),
    }
    for call in calls.values():
        with pytest.raises(ReadOnlyStoreError):
            call()
    assert not (roots[1] / "backups").exists()
    assert [r["subject"] for r in reader.iter_records()] == ["first"]


def test_read_only_error_is_a_store_error() -> None:
    assert issubclass(ReadOnlyStoreError, StoreError)


def test_r3_reading_leaves_the_database_file_byte_identical(roots: tuple[Path, Path]) -> None:
    db = roots[1] / "canon.db"
    before_bytes, before_tables = db.read_bytes(), _tables(db)
    reader = _reader(roots)
    assert [r["subject"] for r in reader.iter_records()] == ["first"]
    assert reader.list_records("contract:setting")
    assert reader.change_token()
    assert list(reader.read_history()) is not None
    errors: list[str] = []
    reader.check_integrity(errors)
    assert errors == []
    assert db.read_bytes() == before_bytes
    assert _tables(db) == before_tables


def test_r4_missing_database_raises_and_creates_nothing(tmp_path: Path) -> None:
    config_root, data_root = tmp_path / "meta", tmp_path / "data"
    config_root.mkdir()
    (config_root / "config.json").write_text(json.dumps(new_config({"contract": "0.1.0"})))
    reader = SqliteBackend(config_root, data_root, read_only=True)
    assert not reader.has_record_collection()
    with pytest.raises(StoreNotInitializedError, match=r"canon\.db"):
        list(reader.iter_records())
    with pytest.raises(StoreNotInitializedError):
        reader.change_token()
    assert not data_root.exists()


def test_r5_reads_committed_records_while_a_write_transaction_is_open(
    roots: tuple[Path, Path],
) -> None:
    writer = SqliteBackend(roots[0], roots[1])
    reader = _reader(roots)
    with writer.transaction():
        writer.create_record(_record("pending"))
        assert [r["subject"] for r in reader.iter_records()] == ["first"]
    assert sorted(r["subject"] for r in reader.iter_records()) == ["first", "pending"]
