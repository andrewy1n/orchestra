"""SQLite materialized records and immutable operation chains."""

from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from orchestra.canon.errors import StaleWriteError, StoreError
from orchestra.canon.git_backend import run_git
from orchestra.canon.metadata import MetadataFiles
from orchestra.canon.oplog import fold
from orchestra.canon.paths import validate_record_id, validate_record_type
from orchestra.canon.record import prepare_record
from orchestra.canon.revision import compute_revision, with_revision
from orchestra.canon.types import JsonObject, Record, StoredOp


def _decide_create(
    current: dict[str, Any] | None, record: dict[str, Any]
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if current is not None:
        return "rejected_exists", current, {"conflict_revision": current.get("revision")}
    return "accepted", with_revision(prepare_record(record)), {}


def _decide_write(
    current: dict[str, Any] | None,
    record: dict[str, Any],
    expected_revision: object,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if current is not None:
        if expected_revision is None:
            return (
                "rejected_missing_expected",
                current,
                {"conflict_revision": current.get("revision")},
            )
        if expected_revision != current.get("revision"):
            return "rejected_stale", current, {"conflict_revision": current.get("revision")}
    return "accepted", with_revision(prepare_record(record)), {}


_SCHEMA = """
CREATE TABLE IF NOT EXISTS ops (
    record_id TEXT NOT NULL, seq INTEGER NOT NULL, op_json TEXT NOT NULL,
    PRIMARY KEY (record_id, seq)
);
CREATE TRIGGER IF NOT EXISTS ops_no_update BEFORE UPDATE ON ops
BEGIN SELECT RAISE(ABORT, 'ops are immutable'); END;
CREATE TRIGGER IF NOT EXISTS ops_no_delete BEFORE DELETE ON ops
BEGIN SELECT RAISE(ABORT, 'ops are immutable'); END;
CREATE TABLE IF NOT EXISTS records (
    record_id TEXT PRIMARY KEY, record_type TEXT NOT NULL, subject TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL, revision TEXT NOT NULL, recorded_at TEXT NOT NULL,
    payload_json TEXT NOT NULL, body TEXT NOT NULL, relationships_json TEXT NOT NULL,
    record_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS records_subject ON records(record_type, subject);
CREATE INDEX IF NOT EXISTS records_state ON records(record_type, lifecycle_state);
CREATE TABLE IF NOT EXISTS revisions (
    record_id TEXT NOT NULL, revision TEXT NOT NULL, record_json TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (record_id, revision)
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
INSERT OR IGNORE INTO meta VALUES ('format', 'canon-sqlite/1');
"""


class SqliteBackend:
    @staticmethod
    def global_data_root(config_root: Path) -> Path:
        repository_root = config_root.parent
        try:
            result = run_git(
                repository_root,
                "rev-parse",
                "--git-common-dir",
                capture_output=True,
                text=True,
            )
        except OSError:
            result = None
        if result is not None and result.returncode == 0 and result.stdout.strip():
            common_dir = Path(result.stdout.strip())
            if not common_dir.is_absolute():
                common_dir = repository_root / common_dir
            repository_name = common_dir.resolve().parent.name
        else:
            repository_name = repository_root.name
        return Path.home().joinpath(".canon", repository_name)

    def __init__(self, config_root: Path, data_root: Path):
        self.config_root = config_root
        self.data_root = data_root
        self.db_path = data_root / "canon.db"
        self._metadata = MetadataFiles(config_root)
        self._active: sqlite3.Connection | None = None
        if self._metadata.has_config():
            self._initialize_database()

    def _initialize_database(self) -> None:
        self.data_root.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        try:
            connection.execute("PRAGMA busy_timeout=10000")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.executescript(_SCHEMA)
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        self.data_root.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        try:
            connection.execute("PRAGMA busy_timeout=10000")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
        except BaseException:
            connection.close()
            raise
        return connection

    @contextlib.contextmanager
    def _reader(self) -> Iterator[sqlite3.Connection]:
        if self._active is not None:
            yield self._active
        else:
            connection = self._connect()
            try:
                yield connection
            finally:
                connection.close()

    @contextlib.contextmanager
    def transaction(self) -> Iterator[None]:
        if self._active is not None:
            name = "nested_" + uuid.uuid4().hex
            connection = self._active
            connection.execute(f"SAVEPOINT {name}")
            try:
                yield
            except BaseException:
                connection.execute(f"ROLLBACK TO {name}")
                raise
            finally:
                connection.execute(f"RELEASE {name}")
            return
        if not self.db_path.is_file():
            self._initialize_database()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._active = connection
            try:
                yield
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
        except sqlite3.Error as exc:
            raise StoreError(f"SQLite transaction failed: {exc}") from exc
        finally:
            self._active = None
            connection.close()

    def load_config(self) -> JsonObject:
        return self._metadata.load_config()

    def has_config(self) -> bool:
        return self._metadata.has_config()

    def write_config(self, config: JsonObject) -> None:
        self._metadata.write_config(config)

    def read_snapshot(self, namespace: str) -> str | None:
        return self._metadata.read_snapshot(namespace)

    def write_snapshot(self, namespace: str, text: str) -> None:
        self._metadata.write_snapshot(namespace, text)

    def is_absent(self) -> bool:
        return self._metadata.is_absent()

    def init(self, config: JsonObject, snapshots: dict[str, str] | None = None) -> str:
        if self.has_config():
            self.load_config()
            return "already_initialized"
        for namespace, text in (snapshots or {}).items():
            self.write_snapshot(namespace, text)
        self.write_config(config)
        if not self.db_path.is_file():
            self._initialize_database()
        return "initialized"

    @staticmethod
    def _validate_key(record_type: str, record_id: str) -> None:
        try:
            validate_record_type(record_type)
            validate_record_id(record_id)
        except ValueError as exc:
            raise StoreError(str(exc)) from exc

    def _chain(self, connection: sqlite3.Connection, record_id: str) -> list[dict[str, Any]]:
        return [
            {**json.loads(row[1]), "seq": row[0]}
            for row in connection.execute(
                "SELECT seq, op_json FROM ops WHERE record_id=? ORDER BY seq",
                (record_id,),
            )
        ]

    def _materialize(self, connection: sqlite3.Connection, record: dict[str, Any]) -> None:
        connection.execute(
            "INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(record_id) DO UPDATE SET "
            "record_type=excluded.record_type, subject=excluded.subject, "
            "lifecycle_state=excluded.lifecycle_state, revision=excluded.revision, "
            "recorded_at=excluded.recorded_at, payload_json=excluded.payload_json, "
            "body=excluded.body, relationships_json=excluded.relationships_json, "
            "record_json=excluded.record_json",
            (
                record["id"],
                record["record_type"],
                record["subject"],
                record["lifecycle_state"],
                record["revision"],
                record["recorded_at"],
                json.dumps(record.get("payload", {})),
                record.get("body", ""),
                json.dumps(record.get("relationships", {})),
                json.dumps(record),
            ),
        )
        connection.execute(
            "INSERT OR IGNORE INTO revisions(record_id, revision, record_json) VALUES (?, ?, ?)",
            (record["id"], record["revision"], json.dumps(record)),
        )

    def _write(
        self,
        record: dict[str, Any],
        *,
        create: bool,
        expected_revision: object = None,
        archive_prior: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record_id = record["id"]
        self._validate_key(record["record_type"], record_id)
        with self.transaction(), self._reader() as connection:
            chain = self._chain(connection, record_id)
            current = fold(chain)
            outcome, state, _ = (
                _decide_create(current, record)
                if create
                else _decide_write(current, record, expected_revision)
            )
            if outcome == "rejected_exists":
                raise StoreError(f"record already exists: {record_id}")
            if outcome == "rejected_missing_expected":
                raise StoreError(f"record {record_id} exists; expected revision required")
            if outcome == "rejected_stale":
                assert current is not None
                raise StaleWriteError(
                    f"stale write for {record_id}: expected {expected_revision}, got {current['revision']}"
                )
            op = {
                "op_id": uuid.uuid4().hex,
                "kind": "create" if create else "write",
                "outcome": "accepted",
                "record": state,
            }
            connection.execute(
                "INSERT INTO ops VALUES (?, ?, ?)",
                (record_id, chain[-1]["seq"] + 1 if chain else 1, json.dumps(op)),
            )
            self._materialize(connection, state)
            if archive_prior is not None and current is not None:
                self.archive_history(archive_prior)
            return state

    def create_record(self, record: Record) -> Record:
        return self._write(record, create=True)

    def write_record(
        self,
        record: Record,
        *,
        expected_revision: object = None,
        archive_prior: Record | None = None,
    ) -> Record:
        return self._write(
            record,
            create=False,
            expected_revision=expected_revision,
            archive_prior=archive_prior,
        )

    def read_record(self, record_type: str, record_id: str) -> Record:
        self._validate_key(record_type, record_id)
        with self._reader() as connection:
            row = connection.execute(
                "SELECT record_json FROM records WHERE record_id=? AND record_type=?",
                (record_id, record_type),
            ).fetchone()
        if row is None:
            raise StoreError(f"unknown record: {record_id}")
        record = json.loads(row[0])
        if record.get("revision") != compute_revision(record):
            raise StoreError(f"revision tamper detected for {record_id}")
        return record

    def iter_records(
        self, record_type: str | None = None, *, errors: list[str] | None = None
    ) -> Iterator[Record]:
        with self._reader() as connection:
            rows = connection.execute(
                "SELECT record_json FROM records"
                + (" WHERE record_type=?" if record_type is not None else "")
                + " ORDER BY record_type, record_id",
                (record_type,) if record_type is not None else (),
            ).fetchall()
        for row in rows:
            try:
                record = json.loads(row[0])
                if record.get("revision") != compute_revision(record):
                    raise StoreError(f"revision tamper detected for {record.get('id')}")
            except (ValueError, StoreError) as exc:
                if errors is None:
                    raise StoreError(str(exc)) from exc
                errors.append(str(exc))
                continue
            yield record

    def list_records(
        self, record_type: str | None = None, lifecycle_state: str | None = None
    ) -> list[Record]:
        return [
            record
            for record in self.iter_records(record_type)
            if lifecycle_state is None or record.get("lifecycle_state") == lifecycle_state
        ]

    def record_exists(self, record_type: str, record_id: str) -> bool:
        self._validate_key(record_type, record_id)
        with self._reader() as connection:
            return (
                connection.execute(
                    "SELECT 1 FROM records WHERE record_id=? AND record_type=?",
                    (record_id, record_type),
                ).fetchone()
                is not None
            )

    def new_id(self) -> str:
        return f"rec-{uuid.uuid4()}"

    def archive_history(self, record: Record) -> None:
        self._validate_key(record["record_type"], record["id"])
        with self.transaction(), self._reader() as connection:
            row = connection.execute(
                "SELECT record_json FROM revisions WHERE record_id=? AND revision=?",
                (record["id"], record["revision"]),
            ).fetchone()
            if row is not None and json.loads(row[0]) != record:
                raise StoreError(f"history snapshot conflict for {record['id']}")
            connection.execute(
                "INSERT INTO revisions VALUES (?, ?, ?, 1) ON CONFLICT(record_id, revision) DO UPDATE SET archived=1",
                (record["id"], record["revision"], json.dumps(record)),
            )

    def read_history(self) -> Iterator[Record]:
        with self._reader() as connection:
            rows = connection.execute(
                "SELECT record_json FROM revisions WHERE archived=1 ORDER BY record_id, revision"
            ).fetchall()
        for row in rows:
            yield json.loads(row[0])

    def history_exists(self, record_type: str, record_id: str, revision: str) -> bool:
        self._validate_key(record_type, record_id)
        with self._reader() as connection:
            row = connection.execute(
                "SELECT record_json FROM revisions WHERE record_id=? AND revision=? AND archived=1",
                (record_id, revision),
            ).fetchone()
        return row is not None and json.loads(row[0])["record_type"] == record_type

    def delete_history_snapshot(self, record_type: str, record_id: str, revision: str) -> None:
        self._validate_key(record_type, record_id)
        with self.transaction(), self._reader() as connection:
            connection.execute(
                "UPDATE revisions SET archived=0 WHERE record_id=? AND revision=?",
                (record_id, revision),
            )

    def delete_record(self, record_type: str, record_id: str) -> None:
        self._validate_key(record_type, record_id)
        with self.transaction(), self._reader() as connection:
            chain = self._chain(connection, record_id)
            if not self.record_exists(record_type, record_id):
                return
            op = {
                "op_id": uuid.uuid4().hex,
                "kind": "delete",
                "outcome": "accepted",
                "record": None,
            }
            connection.execute(
                "INSERT INTO ops VALUES (?, ?, ?)",
                (record_id, chain[-1]["seq"] + 1, json.dumps(op)),
            )
            connection.execute("DELETE FROM records WHERE record_id=?", (record_id,))
            connection.execute("DELETE FROM revisions WHERE record_id=?", (record_id,))

    def iter_chains(self) -> Iterator[tuple[str, list[StoredOp]]]:
        with self._reader() as connection:
            chains = [
                (row[0], self._chain(connection, row[0]))
                for row in connection.execute(
                    "SELECT DISTINCT record_id FROM ops ORDER BY record_id"
                ).fetchall()
            ]
        yield from chains

    def import_op(self, record_type: str, record_id: str, op: StoredOp) -> None:
        self._validate_key(record_type, record_id)
        with self.transaction(), self._reader() as connection:
            connection.execute(
                "INSERT INTO ops VALUES (?, ?, ?)",
                (
                    record_id,
                    op["seq"],
                    json.dumps({key: value for key, value in op.items() if key != "seq"}),
                ),
            )

    def import_record(self, record: Record) -> None:
        self._validate_key(record["record_type"], record["id"])
        with self.transaction(), self._reader() as connection:
            if self.record_exists(record["record_type"], record["id"]):
                raise StoreError(f"record already exists: {record['id']}")
            self._materialize(connection, record)

    def is_empty(self) -> bool:
        with self._reader() as connection:
            return not any(
                connection.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
                for table in ("ops", "records", "revisions")
            )

    def check_integrity(self, errors: list[str], *, immutability: bool = True) -> None:
        with self._reader() as connection:
            for row in connection.execute("PRAGMA integrity_check"):
                if row[0] != "ok":
                    errors.append(f"SQLite integrity: {row[0]}")
            rows = connection.execute("SELECT * FROM records").fetchall()
            records: dict[str, dict[str, Any]] = {}
            for row in rows:
                try:
                    record = json.loads(row[9])
                    records[row[0]] = record
                    columns = (
                        record["id"],
                        record["record_type"],
                        record["subject"],
                        record["lifecycle_state"],
                        record["revision"],
                        record["recorded_at"],
                        json.dumps(record.get("payload", {})),
                        record.get("body", ""),
                        json.dumps(record.get("relationships", {})),
                    )
                    if row[:9] != columns or record["revision"] != compute_revision(record):
                        errors.append(f"{row[0]}: materialized record differs from stored content")
                except (ValueError, KeyError, TypeError) as exc:
                    errors.append(f"{row[0]}: malformed materialized record: {exc}")
            for record_id, ops in self.iter_chains():
                if fold(ops) != records.pop(record_id, None):
                    errors.append(f"{record_id}: materialized record differs from op fold")
            for record_id in records:
                errors.append(f"{record_id}: materialized record has no op chain")
            for record_id, revision, text, archived in connection.execute(
                "SELECT * FROM revisions"
            ):
                try:
                    snapshot = json.loads(text)
                    if (
                        snapshot.get("id") != record_id
                        or snapshot.get("revision") != revision
                        or compute_revision(snapshot) != revision
                    ):
                        errors.append(f"{record_id}: history tamper detected")
                    if archived and not self.record_exists(snapshot["record_type"], record_id):
                        errors.append(f"{record_id}: history snapshot has no live record")
                except (ValueError, KeyError, TypeError) as exc:
                    errors.append(f"{record_id}: malformed history snapshot: {exc}")

    def has_record_collection(self) -> bool:
        return self.db_path.is_file()

    def same_store(self, other: object) -> bool:
        return (
            isinstance(other, SqliteBackend) and self.db_path.resolve() == other.db_path.resolve()
        )

    def change_token(self) -> str:
        with self._reader() as connection:
            rows = connection.execute(
                "SELECT record_id, revision FROM records ORDER BY record_id"
            ).fetchall()
        return hashlib.sha256(json.dumps(rows).encode()).hexdigest()

    def backup(self, keep: int = 14) -> str:
        if self._active is not None:
            raise StoreError("cannot back up during a write transaction")
        if keep < 1:
            raise StoreError("backup retention must be at least 1")
        directory = self.data_root / "backups"
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
            + "-"
            + uuid.uuid4().hex
            + ".db"
        )
        try:
            with (
                self._reader() as source,
                contextlib.closing(sqlite3.connect(destination)) as target,
            ):
                source.backup(target)
        except (sqlite3.Error, OSError) as exc:
            destination.unlink(missing_ok=True)
            raise StoreError(f"SQLite backup failed: {exc}") from exc
        for expired in sorted(directory.glob("*.db"), reverse=True)[keep:]:
            expired.unlink(missing_ok=True)
        return str(destination)

    def backup_due(self, max_age: timedelta) -> bool:
        directory = self.data_root / "backups"
        backups = (
            [path for path in directory.iterdir() if path.is_file()] if directory.is_dir() else []
        )
        if not backups:
            return True
        newest = max(path.stat().st_mtime for path in backups)
        return datetime.now(timezone.utc).timestamp() - newest > max_age.total_seconds()
