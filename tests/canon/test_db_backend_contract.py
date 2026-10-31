"""Independent acceptance contracts for the SQLite record backend."""

from __future__ import annotations

import contextlib
import io
import json
import multiprocessing
import shutil
import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from orchestra.canon.backend import Backend, open_backend
from orchestra.canon.cli import main
from orchestra.canon.config import new_config
from orchestra.canon.oplog import fold
from orchestra.canon.project import Binding, Project, open_store
from orchestra.canon.revision import compute_revision
from orchestra.canon.errors import StaleWriteError, StoreError

SCHEMA: dict[str, Any] = {
    "namespace": "contract",
    "version": "0.1.0",
    "types": {
        "setting": {
            "purpose": "An editable current setting",
            "lifecycle": "current",
            "fields": {"title": {"type": "string"}},
        }
    },
}


def _open(root: Path, selected: str = "sqlite") -> Backend:
    try:
        backend = open_backend(
            root, {**new_config({"contract": "0.1.0"}), "backend": selected}
        )
    except StoreError as exc:
        raise AssertionError(f"{selected} backend must be selectable: {exc}") from exc
    if selected == "sqlite":
        assert type(backend).__name__ == "SqliteBackend"
    return backend


def _initialize(root: Path, selected: str = "sqlite") -> Backend:
    backend = _open(root, selected)
    backend.init(
        {**new_config({"contract": "0.1.0"}), "backend": selected},
        {"contract": json.dumps(SCHEMA)},
    )
    return backend


def _record(record_id: str, title: str = "initial") -> dict[str, Any]:
    return {
        "id": _record_id(record_id),
        "record_type": "contract:setting",
        "subject": record_id,
        "payload": {"title": title},
        "lifecycle_state": "active",
        "relationships": {},
        "recorded_at": "2026-01-01T00:00:00+00:00",
        "body": "",
    }


def _record_id(label: str) -> str:
    return f"rec-{uuid.uuid5(uuid.NAMESPACE_URL, label)}"


@dataclass(frozen=True)
class DbStore:
    project_root: Path
    root: Path
    data_root: Path

    @property
    def project(self) -> Project:
        self.backend
        return Project(
            self.project_root, self.root, Binding("global", "store-binding.json")
        )

    @property
    def db(self) -> Path:
        self.backend
        path = self.data_root / "canon.db"
        assert path.is_file(), (
            "SQLite store must persist canon.db at the bound global path"
        )
        return path

    @property
    def backend(self) -> Backend:
        if not (self.root / "config.json").is_file():
            return _initialize(self.root)
        return _open(self.root)


@pytest.fixture
def db_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> DbStore:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    repo = tmp_path / "contract-repo"
    (repo / ".canon").mkdir(parents=True)
    (repo / ".canon" / "store-binding.json").write_text('{"store":"global"}')
    return DbStore(repo, repo / ".canon", home / ".canon" / repo.name)


def _snapshot(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return "\n".join(connection.iterdump())


def _sql_name(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _cli(project: Project, command: str) -> tuple[int, str]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            code = main(["--root", str(project.project_root), command])
        except SystemExit as exc:
            code = int(exc.code) if isinstance(exc.code, int) else 1
    return code, output.getvalue()


def test_sqlite_implements_backend(tmp_path: Path) -> None:
    backend = _initialize(tmp_path / "store")
    assert isinstance(backend, Backend)
    stored = backend.create_record(_record("contract-record"))
    assert backend.read_record("contract:setting", stored["id"]) == stored


def test_config_selects_sqlite_backend(tmp_path: Path) -> None:
    root = tmp_path / "store"
    _initialize(root)
    selected = open_backend(root)
    assert type(selected).__name__ == "SqliteBackend"
    assert selected.load_config()["backend"] == "sqlite"


def test_global_binding_places_database_under_temporary_home(db_store: DbStore) -> None:
    db_store.backend
    try:
        selected = open_store(db_store.project_root)
    except Exception as exc:
        raise AssertionError(
            f"Global binding must open repository metadata and its global database: {exc}"
        ) from exc
    assert selected.store_path == db_store.root
    assert db_store.project.binding.location == "global"
    assert db_store.project.store_path == db_store.root
    assert db_store.db == Path.home() / ".canon" / "contract-repo" / "canon.db"
    assert (db_store.root / "config.json").is_file()
    assert (db_store.root / "schemas" / "contract.json").is_file()
    assert (db_store.project.project_root / ".canon" / "store-binding.json").is_file()


def test_database_contains_required_tables(db_store: DbStore) -> None:
    with sqlite3.connect(db_store.db) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert {"ops", "records", "revisions", "meta"} <= tables


@pytest.mark.parametrize("verb", ["UPDATE", "DELETE"])
def test_op_triggers_reject_mutation(db_store: DbStore, verb: str) -> None:
    db_store.backend.create_record(_record("immutable-op"))
    before = _snapshot(db_store.db)
    with sqlite3.connect(db_store.db) as connection:
        column = connection.execute("PRAGMA table_info(ops)").fetchone()[1]
        sql = (
            "DELETE FROM ops"
            if verb == "DELETE"
            else f"UPDATE ops SET {_sql_name(column)}={_sql_name(column)}"
        )
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute(sql)
    assert _snapshot(db_store.db) == before


@pytest.mark.parametrize("table", ["ops", "records", "revisions"])
def test_write_rolls_back_all_tables_on_sql_failure(
    db_store: DbStore, table: str
) -> None:
    db_store.backend.create_record(_record("existing"))
    with sqlite3.connect(db_store.db) as connection:
        connection.execute(
            f"CREATE TRIGGER contract_abort BEFORE INSERT ON {_sql_name(table)} "
            "BEGIN SELECT RAISE(ABORT, 'contract injected failure'); END"
        )
    before = _snapshot(db_store.db)
    with pytest.raises((StoreError, sqlite3.DatabaseError)):
        db_store.backend.create_record(_record("must-roll-back"))
    assert _snapshot(db_store.db) == before
    assert not db_store.backend.record_exists(
        "contract:setting", _record_id("must-roll-back")
    )


def test_writes_begin_immediate_and_use_ten_second_busy_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_connect = sqlite3.connect
    traces: list[tuple[str, int]] = []
    connections: list[sqlite3.Connection] = []

    def connect(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        connection = real_connect(*args, **kwargs)
        connections.append(connection)

        def trace(statement: str) -> None:
            if statement.strip().upper().startswith("BEGIN"):
                timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]
                traces.append((statement.strip().upper(), timeout))

        connection.set_trace_callback(trace)
        return connection

    monkeypatch.setattr(sqlite3, "connect", connect)
    backend = _initialize(tmp_path / "trace-store")
    traces.clear()
    first = backend.create_record(_record("trace-record"))
    backend.write_record(
        {**first, "body": "changed"},
        expected_revision=first["revision"],
        archive_prior=first,
    )
    assert traces, "Record writes must open SQLite transactions"
    assert all(statement == "BEGIN IMMEDIATE" for statement, _ in traces), traces
    assert all(timeout == 10_000 for _, timeout in traces), traces
    for connection in connections:
        connection.close()


def test_stale_write_raises_stale_write_error(db_store: DbStore) -> None:
    backend = db_store.backend
    first = backend.create_record(_record("stale"))
    second = backend.write_record(
        {**first, "body": "new"},
        expected_revision=first["revision"],
        archive_prior=first,
    )
    with pytest.raises(StaleWriteError):
        backend.write_record(
            {**first, "body": "lost"},
            expected_revision=first["revision"],
            archive_prior=first,
        )
    assert backend.read_record("contract:setting", first["id"]) == second


@pytest.mark.parametrize("rejection", ["duplicate", "stale", "missing_expected"])
def test_rejected_write_leaves_database_unchanged(
    db_store: DbStore, rejection: str
) -> None:
    backend = db_store.backend
    first = backend.create_record(_record("rejected"))
    current = backend.write_record(
        {**first, "body": "new"},
        expected_revision=first["revision"],
        archive_prior=first,
    )
    before = _snapshot(db_store.db)
    with pytest.raises(StoreError):
        if rejection == "duplicate":
            backend.create_record(_record("rejected"))
        else:
            expected = first["revision"] if rejection == "stale" else None
            backend.write_record(
                {**current, "body": "lost"},
                expected_revision=expected,
                archive_prior=current,
            )
    assert _snapshot(db_store.db) == before


def test_failed_supersede_rolls_back_predecessor_and_successor(
    db_store: DbStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = db_store.project.create(
        record_type="contract:setting", subject="setting", payload={"title": "old"}
    )
    backend_class = type(db_store.backend)
    original_create = backend_class.create_record

    def fail_successor(self: Backend, record: dict[str, Any]) -> dict[str, Any]:
        if record.get("relationships", {}).get("supersedes") == [old["id"]]:
            raise StoreError("contract successor failure")
        return original_create(self, record)

    monkeypatch.setattr(backend_class, "create_record", fail_successor)
    before = _snapshot(db_store.db)
    with pytest.raises(StoreError, match="contract successor failure"):
        db_store.project.supersede(old["id"], payload={"title": "new"})
    assert _snapshot(db_store.db) == before
    assert db_store.project.records() == [old]


def _write_worker(
    root: str, worker: int, count: int, barrier: Any, results: Any
) -> None:
    try:
        real_connect = sqlite3.connect
        begins: list[str] = []

        def connect(*args: Any, **kwargs: Any) -> sqlite3.Connection:
            connection = real_connect(*args, **kwargs)

            def trace(statement: str) -> None:
                if statement.strip().upper().startswith("BEGIN"):
                    begins.append(statement.strip().upper())

            connection.set_trace_callback(trace)
            return connection

        sqlite3.connect = connect
        backend = _open(Path(root))
        barrier.wait(timeout=20)
        for index in range(count):
            backend.create_record(_record(f"worker-{worker}-record-{index}"))
        assert begins and all(statement == "BEGIN IMMEDIATE" for statement in begins), (
            begins
        )
        results.put(("ok", worker))
    except Exception as exc:
        results.put(("error", repr(exc)))
        raise


def _contested_worker(
    root: str, record: dict[str, Any], body: str, barrier: Any, results: Any
) -> None:
    try:
        backend = _open(Path(root))
        barrier.wait(timeout=20)
        backend.write_record(
            {**record, "body": body},
            expected_revision=record["revision"],
            archive_prior=record,
        )
        results.put(("ok", body))
    except StaleWriteError:
        results.put(("stale", body))
    except Exception as exc:
        results.put(("error", repr(exc)))
        raise


def _join(workers: list[Any]) -> None:
    try:
        for worker in workers:
            worker.join(timeout=30)
        assert all(not worker.is_alive() for worker in workers), "Worker stalled"
        assert [worker.exitcode for worker in workers] == [0] * len(workers)
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=5)


def test_multiprocess_distinct_writes_preserve_records_and_single_ops(
    db_store: DbStore,
) -> None:
    db_store.backend
    context = multiprocessing.get_context("spawn")
    count, per_worker = 4, 12
    barrier, results = context.Barrier(count), context.Queue()
    workers = [
        context.Process(
            target=_write_worker,
            args=(str(db_store.root), index, per_worker, barrier, results),
        )
        for index in range(count)
    ]
    for worker in workers:
        worker.start()
    _join(workers)
    outcomes = [results.get(timeout=5) for _ in workers]
    assert all(outcome[0] == "ok" for outcome in outcomes), outcomes
    backend = db_store.backend
    records = backend.list_records()
    assert len(records) == count * per_worker
    assert {record["id"] for record in records} == {
        _record_id(f"worker-{worker}-record-{index}")
        for worker in range(count)
        for index in range(per_worker)
    }
    chains = dict(backend.iter_chains())
    assert set(chains) == {record["id"] for record in records}
    assert all(len(ops) == 1 for ops in chains.values())
    assert all(fold(chains[record["id"]]) == record for record in records)
    with sqlite3.connect(db_store.db) as connection:
        assert (
            connection.execute("SELECT count(*) FROM ops").fetchone()[0]
            == count * per_worker
        )
        assert (
            connection.execute("SELECT count(*) FROM records").fetchone()[0]
            == count * per_worker
        )
        assert (
            connection.execute("SELECT count(*) FROM revisions").fetchone()[0]
            == count * per_worker
        )


def test_multiprocess_same_revision_has_exactly_one_winner(db_store: DbStore) -> None:
    first = db_store.backend.create_record(_record("contested"))
    context = multiprocessing.get_context("spawn")
    barrier, results = context.Barrier(2), context.Queue()
    workers = [
        context.Process(
            target=_contested_worker,
            args=(str(db_store.root), first, body, barrier, results),
        )
        for body in ("one", "two")
    ]
    for worker in workers:
        worker.start()
    _join(workers)
    outcomes = [results.get(timeout=5) for _ in workers]
    assert sorted(outcome[0] for outcome in outcomes) == ["ok", "stale"], outcomes
    winner = next(body for outcome, body in outcomes if outcome == "ok")
    stored = db_store.backend.read_record("contract:setting", first["id"])
    assert stored["body"] == winner
    chain = dict(db_store.backend.iter_chains())[first["id"]]
    assert len(chain) == 2
    assert fold(chain) == stored


def test_database_uses_wal(db_store: DbStore) -> None:
    with sqlite3.connect(db_store.db) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_cli_validate_accepts_valid_database(db_store: DbStore) -> None:
    first = db_store.project.create(
        record_type="contract:setting", subject="valid", payload={"title": "first"}
    )
    db_store.project.update(first["id"], payload={"title": "second"})
    code, output = _cli(db_store.project, "validate")
    assert code == 0, output


def test_cli_validate_detects_materialized_row_tampering(db_store: DbStore) -> None:
    db_store.backend.create_record(_record("tampered"))
    with sqlite3.connect(db_store.db) as connection:
        columns = connection.execute("PRAGMA table_info(records)").fetchall()
        row = connection.execute("SELECT * FROM records").fetchone()
        changed = False
        for column, value in zip(columns, row):
            if not isinstance(value, str):
                continue
            try:
                decoded = json.loads(value)
            except ValueError:
                continue
            if isinstance(decoded, dict) and decoded.get("id") == _record_id(
                "tampered"
            ):
                decoded["payload"] = {"title": "raw SQL corruption"}
                connection.execute(
                    f"UPDATE records SET {_sql_name(column[1])}=?",
                    (json.dumps(decoded),),
                )
                changed = True
                break
        if not changed:
            names = {column[1] for column in columns}
            assert "subject" in names, (
                "records must expose either its serialized record or subject for corruption probing"
            )
            connection.execute("UPDATE records SET subject='raw SQL corruption'")
    code, output = _cli(db_store.project, "validate")
    assert code != 0, output
    assert "internal" not in output.lower(), output


def test_cli_backup_copies_consistent_database_during_writes(
    db_store: DbStore, tmp_path: Path
) -> None:
    db_store.backend.create_record(_record("backup-seed"))
    context = multiprocessing.get_context("spawn")
    barrier, results = context.Barrier(2), context.Queue()
    worker = context.Process(
        target=_write_worker, args=(str(db_store.root), 0, 30, barrier, results)
    )
    worker.start()
    barrier.wait(timeout=20)
    code, output = _cli(db_store.project, "backup")
    _join([worker])
    assert results.get(timeout=5)[0] == "ok"
    assert code == 0, output
    backups = list((db_store.data_root / "backups").glob("*.db"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        counts = [
            connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("ops", "records", "revisions")
        ]
        assert len(set(counts)) == 1, counts
        assert 1 <= counts[0] <= 31
    restored_repo = tmp_path / "restored-backup"
    restored_metadata = restored_repo / ".canon"
    shutil.copytree(db_store.root, restored_metadata)
    restored_data = Path.home() / ".canon" / restored_repo.name
    restored_data.mkdir(parents=True)
    shutil.copy2(backups[0], restored_data / "canon.db")
    restored = Project(
        restored_repo, restored_metadata, Binding("global", "store-binding.json")
    )
    assert restored.validate() == []
    assert len(restored.records()) == counts[0]


def test_cli_backup_keeps_fourteen_newest_distinct_copies(db_store: DbStore) -> None:
    backend = db_store.backend
    for index in range(17):
        backend.create_record(_record(f"backup-record-{index}"))
        code, output = _cli(db_store.project, "backup")
        assert code == 0, output
    backups = list((db_store.data_root / "backups").glob("*.db"))
    assert len(backups) == 14
    counts: list[int] = []
    for path in backups:
        with sqlite3.connect(path) as connection:
            counts.append(
                connection.execute("SELECT count(*) FROM records").fetchone()[0]
            )
    assert sorted(counts) == list(range(4, 18))


def test_operation_sequence_has_stable_revisions(tmp_path: Path) -> None:
    backend = _initialize(tmp_path / "sqlite", "sqlite")
    current = backend.create_record(_record("same-record"))
    revisions = [current["revision"]]
    for title in ("second", "third"):
        prior = current
        current = backend.write_record(
            {**prior, "payload": {"title": title}},
            expected_revision=prior["revision"],
            archive_prior=prior,
        )
        assert current["revision"] == compute_revision(current)
        revisions.append(current["revision"])
    assert len(set(revisions)) == len(revisions)
    assert sorted(record["revision"] for record in backend.read_history()) == sorted(
        revisions[:-1]
    )


@pytest.fixture(params=["sqlite"], ids=["sqlite"])
def contract_backend(
    request: pytest.FixtureRequest, tmp_path: Path
) -> Callable[[], Backend]:
    return lambda: _initialize(tmp_path / str(request.param), str(request.param))


def test_shared_backend_contract_reads_updates_history_and_chains(
    contract_backend: Callable[[], Backend],
) -> None:
    contract_backend = contract_backend()
    first = contract_backend.create_record(_record("shared-record"))
    updated = contract_backend.write_record(
        {**first, "payload": {"title": "changed"}},
        expected_revision=first["revision"],
        archive_prior=first,
    )
    assert contract_backend.record_exists("contract:setting", first["id"])
    assert contract_backend.read_record("contract:setting", first["id"]) == updated
    assert contract_backend.list_records("contract:setting", "active") == [updated]
    assert list(contract_backend.iter_records("contract:setting")) == [updated]
    assert contract_backend.history_exists(
        "contract:setting", first["id"], first["revision"]
    )
    assert first in list(contract_backend.read_history())
    assert fold(dict(contract_backend.iter_chains())[first["id"]]) == updated
    errors: list[str] = []
    contract_backend.check_integrity(errors)
    assert errors == []
