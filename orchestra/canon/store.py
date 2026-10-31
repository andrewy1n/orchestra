"""JSON filesystem store for schema-bound semantic records.

Mutations never read-modify-write a record file directly: `create_record`
and `write_record` append an immutable op to that record's chain (see
`oplog.py`), then fold the chain to decide accept/reject and to materialize
`records/<type>/<id>.md` -- the same on-disk shape `query.py`, `derive.py`,
and `validation.py` read, so nothing downstream of the materialized store
changed. `expected_revision` conflicts are therefore
detected by folding, not by locking the record file, and concurrent writers
to different (or even the same) record chain never block each other.
Multi-record operations (e.g. supersede) are still not
transactional across records. Validation detects orphan superseded records,
partial lineage, and path/layout tampering.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import time
import uuid
from datetime import timedelta
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any, Iterator

from orchestra.canon.config import CONFIG_NAME, ConfigError, dump_config, validate_config
from orchestra.canon.git_backend import run_git
from orchestra.canon.paths import (
    PathValidationError,
    revision_filename,
    type_dir_name,
    validate_record_id,
    validate_record_type,
)
from orchestra.canon.oplog import CHECKPOINT_KIND, OP_SUFFIX, append_resolved_op, fold, prune_before, purge_chain, read_ops
from orchestra.canon.record_file import (
    RECORD_GLOB,
    RECORD_SUFFIX,
    RecordFileError,
    dump_record,
    load_record,
    prepare_record,
)
from orchestra.canon.revision import compute_revision, with_revision

CHECKPOINT_THRESHOLD = 32

LOCK_FILENAME = ".write.lock"
LOCK_RETRY_ATTEMPTS = 20
LOCK_RETRY_INTERVAL_SECONDS = 0.05


class StoreError(Exception):
    pass


class StaleWriteError(StoreError):
    pass


class StoreNotInitializedError(StoreError):
    pass


class PartialStoreError(StoreError):
    pass


class StoreLockError(StoreError):
    pass


def _load_json_file(path: Path, label: str) -> Any:
    try:
        with path.open() as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise StoreError(f"malformed JSON in {label}: {exc}") from exc


def _load_record_file(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text()
    except OSError as exc:
        raise StoreError(f"cannot read record file {path}: {exc}") from exc
    try:
        return load_record(text, path)
    except RecordFileError as exc:
        raise StoreError(str(exc)) from exc


def _decide_create(current: dict[str, Any] | None, record: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if current is not None:
        return "rejected_exists", current, {"conflict_revision": current.get("revision")}
    new_state = with_revision(prepare_record(record))
    return "accepted", new_state, {}


def _decide_write(
    current: dict[str, Any] | None, record: dict[str, Any], expected_revision: str | None
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if current is not None:
        if expected_revision is None:
            return "rejected_missing_expected", current, {"conflict_revision": current.get("revision")}
        if expected_revision != current.get("revision"):
            return "rejected_stale", current, {"conflict_revision": current.get("revision")}
    new_state = with_revision(prepare_record(record))
    return "accepted", new_state, {}


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.records_dir = root / "records"
        self.history_dir = root / "history"
        self.log_dir = root / "log"
        self.schemas_dir = root / "schemas"

    def config_path(self) -> Path:
        return self.root / CONFIG_NAME

    def snapshot_path(self, namespace: str) -> Path:
        return self.schemas_dir / f"{namespace}.json"

    def lock_path(self) -> Path:
        return self.root / LOCK_FILENAME

    @contextlib.contextmanager
    def write_lock(self) -> Iterator[None]:
        """Advisory single-writer lock for the store, held for one mutating operation.

        Fails fast (after a short bounded retry) instead of blocking forever, since a
        stuck writer should surface as an error, not a hang.
        """
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.lock_path()
        handle = path.open("a+")
        try:
            acquired = False
            holder: str | None = None
            for attempt in range(LOCK_RETRY_ATTEMPTS):
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                    break
                except BlockingIOError:
                    handle.seek(0)
                    holder = handle.read().strip() or None
                    if attempt < LOCK_RETRY_ATTEMPTS - 1:
                        time.sleep(LOCK_RETRY_INTERVAL_SECONDS)
            if not acquired:
                detail = f" (held by {holder})" if holder else ""
                raise StoreLockError(f"store is locked for writing{detail}: {path}")
            handle.seek(0)
            handle.truncate()
            handle.write(f"pid:{os.getpid()}\n")
            handle.flush()
            try:
                yield
            finally:
                handle.seek(0)
                handle.truncate()
                handle.flush()
                # Leave nothing behind to be swept into a commit by `git add -A`.
                with contextlib.suppress(OSError):
                    path.unlink()
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()

    def is_absent(self) -> bool:
        if not self.root.exists():
            return True
        if self.config_path().is_file():
            return False
        return not self._has_partial_content()

    def is_empty(self) -> bool:
        return (
            next(self.iter_records(), None) is None
            and next(self.iter_chains(), None) is None
            and next(self.read_history(), None) is None
        )

    def _has_partial_content(self) -> bool:
        if self.config_path().exists() and not self.config_path().is_file():
            return True
        for base in (self.records_dir, self.history_dir):
            if base.is_dir() and any(base.rglob(RECORD_GLOB)):
                return True
        if self.log_dir.is_dir() and any(self.log_dir.rglob(f"*{OP_SUFFIX}")):
            return True
        return False

    def load_config(self) -> dict[str, Any]:
        if not self.config_path().is_file():
            if self._has_partial_content():
                raise PartialStoreError("store exists without valid config.json")
            raise StoreNotInitializedError("store not initialized")
        data = _load_json_file(self.config_path(), "config.json")
        try:
            return validate_config(data)
        except ConfigError as exc:
            raise StoreError(str(exc)) from exc

    def write_config(self, config: dict[str, Any]) -> None:
        try:
            validate_config(config)
        except ConfigError as exc:
            raise StoreError(str(exc)) from exc
        self._atomic_write(self.config_path(), dump_config(config))

    def write_snapshot(self, namespace: str, text: str) -> None:
        self._atomic_write(self.snapshot_path(namespace), text)

    def type_dir(self, record_type: str) -> Path:
        try:
            dirname = type_dir_name(record_type)
        except PathValidationError as exc:
            raise StoreError(str(exc)) from exc
        return self.records_dir / dirname

    def record_path(self, record_type: str, record_id: str) -> Path:
        try:
            validate_record_type(record_type)
            validate_record_id(record_id)
        except PathValidationError as exc:
            raise StoreError(str(exc)) from exc
        return self.type_dir(record_type) / f"{record_id}{RECORD_SUFFIX}"

    def _chain_dir(self, record_type: str, record_id: str) -> Path:
        try:
            validate_record_type(record_type)
            validate_record_id(record_id)
        except PathValidationError as exc:
            raise StoreError(str(exc)) from exc
        return self.log_dir / type_dir_name(record_type) / record_id

    def history_snapshot_path(self, record_type: str, record_id: str, revision: str) -> Path:
        try:
            validate_record_type(record_type)
            validate_record_id(record_id)
            filename = revision_filename(revision)
        except PathValidationError as exc:
            raise StoreError(str(exc)) from exc
        return self.history_dir / type_dir_name(record_type) / record_id / filename

    def init(self, config: dict[str, Any], snapshots: dict[str, str] | None = None) -> str:
        if self.config_path().is_file():
            self.load_config()
            return "already_initialized"
        if self._has_partial_content():
            raise PartialStoreError("refusing to init over partial store without valid config.json")
        self.root.mkdir(parents=True, exist_ok=True)
        self.records_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        for namespace, text in (snapshots or {}).items():
            self.write_snapshot(namespace, text)
        self.write_config(config)
        return "initialized"

    def _atomic_write(self, path: Path, content: str, *, overwrite: bool = True) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not overwrite and path.exists():
            raise StoreError(f"refusing to overwrite existing file: {path}")
        # Unique per call, not just per target: concurrent writers materializing
        # the same record now race on this path, and a shared tmp name would let
        # one process's replace() steal the file out from under another's.
        tmp = path.with_suffix(f"{path.suffix}.tmp-{uuid.uuid4().hex}")
        try:
            tmp.write_text(content)
            tmp.replace(path)
        finally:
            tmp.unlink(missing_ok=True)

    def _history_content(self, record: dict[str, Any]) -> str:
        return dump_record(record)

    def archive_history(self, record: dict[str, Any]) -> None:
        path = self.history_snapshot_path(
            record["record_type"], record["id"], record["revision"]
        )
        content = self._history_content(record)
        if path.exists():
            existing = path.read_text()
            if existing == content:
                return
            raise StoreError(f"history snapshot conflict at {path}")
        self._atomic_write(path, content, overwrite=False)

    def iter_history(self) -> Iterator[tuple[Path, dict[str, Any]]]:
        if not self.history_dir.is_dir():
            return iter(())
        for path in sorted(self.history_dir.rglob(RECORD_GLOB)):
            snapshot = _load_record_file(path)
            yield path, snapshot

    def _materialize(self, record_type: str, record_id: str, state: dict[str, Any]) -> None:
        self._atomic_write(self.record_path(record_type, record_id), dump_record(state))

    def _maybe_checkpoint(self, chain_dir: Path) -> None:
        """Bound chain growth once it passes a threshold.

        The checkpoint op is appended the same way any other op is (see
        `oplog.append_resolved_op`) -- always "accepted", since it is a
        snapshot rather than a conflicting mutation -- so it is crash-safe
        the same way. Its record is whatever `append_resolved_op` folds
        fresh at the moment it claims its slot, never a state captured
        earlier by the caller: a checkpoint is itself an accepted op, so it
        wins the fold like any other, and baking in a snapshot from before
        its own commit could paper back over an op that landed in between,
        permanently losing it once `prune_before` deletes the pre-checkpoint
        files. Pruning the ops it subsumes is a best-effort cleanup
        afterward: folding a checkpoint plus leftover pre-checkpoint files
        still yields the identical final state, so a crash or race mid-prune
        only costs a temporarily larger chain, never a wrong answer. Safe to
        run concurrently with another writer that just appended one of the
        ops being pruned: that writer already has its own outcome baked into
        the op it wrote and never needs to re-read that specific file.
        """
        if len(read_ops(chain_dir)) < CHECKPOINT_THRESHOLD:
            return
        checkpoint = append_resolved_op(chain_dir, CHECKPOINT_KIND, lambda current: ("accepted", current, {}))
        prune_before(chain_dir, checkpoint["seq"])

    def write_record(
        self,
        record: dict[str, Any],
        *,
        expected_revision: str | None = None,
        archive_prior: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record_type = record["record_type"]
        record_id = record["id"]
        self.record_path(record_type, record_id)  # validate path components early
        chain_dir = self._chain_dir(record_type, record_id)
        state_before: list[dict[str, Any] | None] = []

        def decide(current: dict[str, Any] | None) -> tuple[str, dict[str, Any], dict[str, Any]]:
            state_before.append(current)
            return _decide_write(current, record, expected_revision)

        written = append_resolved_op(chain_dir, "write", decide)
        # Re-fold rather than trust written["record"]: another writer's op may
        # have landed after this one, and that newer state is what belongs on
        # disk -- re-folding never needs this op's own file to still exist.
        # Do this -- and the checkpoint check -- unconditionally, including on
        # a rejected outcome: a chain under heavy contention accumulates far
        # more rejected attempts than accepted ones, and skipping the bound
        # on the reject path is what would let it grow without bound.
        final_state = fold(read_ops(chain_dir))
        assert final_state is not None
        self._materialize(record_type, record_id, final_state)
        self._maybe_checkpoint(chain_dir)
        if written["outcome"] == "rejected_missing_expected":
            raise StoreError(f"record {record_id} exists; expected revision required")
        if written["outcome"] == "rejected_stale":
            raise StaleWriteError(
                f"stale write for {record_id}: expected {expected_revision}, "
                f"got {written.get('conflict_revision')}"
            )
        if state_before[-1] is not None and archive_prior is not None:
            self.archive_history(archive_prior)
        return with_revision(prepare_record(record))

    def create_record(self, record: dict[str, Any]) -> dict[str, Any]:
        record_type = record["record_type"]
        record_id = record["id"]
        self.record_path(record_type, record_id)  # validate path components early
        chain_dir = self._chain_dir(record_type, record_id)
        written = append_resolved_op(chain_dir, "create", lambda current: _decide_create(current, record))
        final_state = fold(read_ops(chain_dir))
        assert final_state is not None
        self._materialize(record_type, record_id, final_state)
        self._maybe_checkpoint(chain_dir)
        if written["outcome"] == "rejected_exists":
            raise StoreError(f"record already exists: {record_id}")
        return with_revision(prepare_record(record))

    def record_exists(self, record_type: str, record_id: str) -> bool:
        return self.record_path(record_type, record_id).is_file()

    def delete_record_file(self, record_type: str, record_id: str) -> None:
        """Remove a record file, e.g. to unwind a partially-written create.

        Silent no-op if already absent, so rollback is safe to call twice. Also
        purges the record's op chain: ids are never reused, so nothing will
        ever append to this chain again, and leaving it behind would only grow
        the log for no reason.
        """
        self.record_path(record_type, record_id).unlink(missing_ok=True)
        purge_chain(self._chain_dir(record_type, record_id))

    def delete_history_snapshot(self, record_type: str, record_id: str, revision: str) -> None:
        """Companion to delete_record_file for append-only types' history snapshot."""
        snapshot = self.history_snapshot_path(record_type, record_id, revision)
        snapshot.unlink(missing_ok=True)
        directory = snapshot.parent
        while directory != self.history_dir and directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
            directory = directory.parent

    def read_record(self, record_type: str, record_id: str) -> dict[str, Any]:
        path = self.record_path(record_type, record_id)
        if not path.is_file():
            raise StoreError(f"unknown record: {record_id}")
        record = _load_record_file(path)
        if record.get("revision") != compute_revision(record):
            raise StoreError(f"revision tamper detected for {record_id}")
        return record

    def iter_records(
        self, record_type: str | None = None, *, errors: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        if errors is not None:
            for record in load_records_for_validation(self.root, errors):
                if record_type is None or record["record_type"] == record_type:
                    yield record
            return
        if not self.records_dir.is_dir():
            return iter(())
        if record_type is not None:
            type_dirs = [self.type_dir(record_type)]
        else:
            type_dirs = sorted(p for p in self.records_dir.iterdir() if p.is_dir())
        for type_dir in type_dirs:
            stray = sorted(
                p.name
                for p in type_dir.glob("*")
                if p.is_file() and p.suffix != RECORD_SUFFIX
            )
            if stray:
                # Silently skipping these would report an unmigrated store as empty,
                # which reads as "valid" everywhere downstream.
                raise StoreError(
                    f"unrecognized record files in {type_dir}: {stray}; "
                    f"expected {RECORD_SUFFIX}"
                )
            for path in sorted(type_dir.glob(RECORD_GLOB)):
                record = _load_record_file(path)
                if record.get("revision") != compute_revision(record):
                    raise StoreError(
                        f"revision tamper detected for {record.get('id', path.name)}"
                    )
                yield record

    def list_records(
        self,
        record_type: str | None = None,
        lifecycle_state: str | None = None,
    ) -> list[dict[str, Any]]:
        records = list(self.iter_records(record_type))
        if lifecycle_state is not None:
            records = [r for r in records if r.get("lifecycle_state") == lifecycle_state]
        return records

    def new_id(self) -> str:
        return f"rec-{uuid.uuid4()}"

    def __str__(self) -> str:
        return str(self.root)

    def has_config(self) -> bool:
        return self.config_path().is_file()

    def same_store(self, other: object) -> bool:
        return isinstance(other, Store) and self.root.resolve() == other.root.resolve()

    def has_record_collection(self) -> bool:
        return self.records_dir.is_dir()

    def read_snapshot(self, namespace: str) -> str | None:
        snapshot = self.snapshot_path(namespace)
        return snapshot.read_text(encoding="utf-8") if snapshot.is_file() else None

    def transaction(self) -> contextlib.AbstractContextManager[None]:
        return self.write_lock()

    def read_history(self) -> Iterator[dict[str, Any]]:
        for _, snapshot in self.iter_history():
            yield snapshot

    def history_exists(self, record_type: str, record_id: str, revision: str) -> bool:
        return self.history_snapshot_path(record_type, record_id, revision).is_file()

    def delete_record(self, record_type: str, record_id: str) -> None:
        self.delete_record_file(record_type, record_id)

    def iter_chains(self) -> Iterator[tuple[str, list[dict[str, Any]]]]:
        if self.log_dir.is_dir():
            for chain_dir in sorted(self.log_dir.glob("*/*")):
                if chain_dir.is_dir():
                    ops = read_ops(chain_dir)
                    if ops:
                        yield chain_dir.name, ops

    def import_op(self, record_type: str, record_id: str, op: dict[str, Any]) -> None:
        from orchestra.canon.oplog import _seq_name

        content = {key: value for key, value in op.items() if key != "seq"}
        text = json.dumps(content, sort_keys=True, separators=(",", ":"))
        self._atomic_write(self._chain_dir(record_type, record_id) / _seq_name(op["seq"]), text, overwrite=False)

    def import_record(self, record: dict[str, Any]) -> None:
        self._atomic_write(self.record_path(record["record_type"], record["id"]), dump_record(record), overwrite=False)

    def check_integrity(self, errors: list[str], *, immutability: bool = True) -> None:
        validate_history(self.root, load_records_for_validation(self.root, []), errors)
        if immutability:
            validate_immutability(self.root, errors)

    def backup(self, keep: int = 14) -> str:
        raise StoreError("backup requires a SQLite store")

    def backup_due(self, max_age: timedelta) -> bool:
        return False

    def change_token(self) -> str:
        digest = hashlib.sha1()
        try:
            with os.scandir(self.records_dir) as entries:
                for entry in sorted(entries, key=lambda item: item.name):
                    if entry.is_dir():
                        digest.update(f"{entry.name}\0{entry.stat().st_mtime_ns}\n".encode())
        except OSError:
            pass
        return digest.hexdigest()


def _validate_history_path_layout(path: Path, history_root: Path, snapshot: dict[str, Any], errors: list[str]) -> None:
    try:
        rel = path.relative_to(history_root)
    except ValueError:
        errors.append(f"history snapshot outside history root: {path}")
        return
    parts = rel.parts
    if len(parts) != 3:
        errors.append(f"history snapshot bad layout: {path}")
        return
    type_dir, record_id, filename = parts
    record_type = snapshot.get("record_type")
    snapshot_id = snapshot.get("id")
    revision = snapshot.get("revision")
    if not record_type or not snapshot_id or not revision:
        errors.append(f"history snapshot missing type/id/revision: {path}")
        return
    try:
        expected_type_dir = type_dir_name(record_type)
        expected_filename = revision_filename(revision)
    except ValueError as exc:
        errors.append(f"history snapshot invalid path fields: {path}: {exc}")
        return
    if type_dir != expected_type_dir:
        errors.append(
            f"history snapshot type directory mismatch: {path} expected {expected_type_dir!r}"
        )
    if record_id != snapshot_id:
        errors.append(
            f"history snapshot record id mismatch: {path} expected parent {snapshot_id!r}"
        )
    if filename != expected_filename:
        errors.append(
            f"history snapshot revision filename mismatch: {path} expected {expected_filename!r}"
        )


def validate_history(store_root: Path, records: list[dict[str, Any]], errors: list[str]) -> None:
    history_root = store_root / "history"
    if not history_root.is_dir():
        return
    known_ids = {record["id"] for record in records}
    for path in sorted(history_root.rglob(RECORD_GLOB)):
        try:
            snapshot = load_record(path.read_text(), path)
        except RecordFileError as exc:
            errors.append(f"history malformed record file {path}: {exc}")
            continue
        if not isinstance(snapshot, dict):
            errors.append(f"history snapshot must be a record object: {path}")
            continue
        if snapshot.get("revision") != compute_revision(snapshot):
            errors.append(f"history tamper detected: {path}")
            continue
        _validate_history_path_layout(path, history_root, snapshot, errors)
        record_id = snapshot.get("id")
        record_type = snapshot.get("record_type")
        if record_id not in known_ids:
            errors.append(f"history snapshot {path.name}: unknown record id {record_id!r}")
        if record_type and record_id:
            expected = (
                store_root
                / "records"
                / type_dir_name(record_type)
                / f"{record_id}{RECORD_SUFFIX}"
            )
            if not expected.is_file():
                errors.append(f"history snapshot {path.name}: no live record for {record_id}")


def _run_git(cwd: Path, *args: str) -> CompletedProcess[str] | None:
    try:
        return run_git(cwd, *args, capture_output=True, text=True)
    except OSError:
        return None


def _git_toplevel(path: Path) -> Path | None:
    result = _run_git(path, "rev-parse", "--show-toplevel")
    if result is None or result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def _git_head_exists(repo_root: Path) -> bool:
    result = _run_git(repo_root, "rev-parse", "--verify", "-q", "HEAD")
    return result is not None and result.returncode == 0


def _authorized_record_rewrite(store_root: Path, records_rel: str, offending: str) -> bool:
    """True when a modified `records/` path is a rewrite the store's own op
    log can account for, not an out-of-band edit.

    `oplog.append_resolved_op` bakes the exact record dict into every
    accepted create/write op, and `Store._materialize` always writes
    `dump_record(fold(read_ops(chain_dir)))` -- the chain's folded state --
    to the record path (see `store.py`). So if the record currently on disk
    equals that fold, some accepted op in *this record's own chain*
    produced it, whether or not that op or the record file has been
    committed yet. Nothing here needs the record file, or the op that
    produced it, to be committed -- only that they agree with each other.

    Deliberately does not accept a bare "revision is self-consistent"
    record: `revision` is a public, deterministic hash of the record's own
    content (see `revision.py`), so a hand-edited record paired with a
    hand-recomputed revision proves nothing.

    What this catches is an edit made without going through the runtime --
    the realistic case, an agent or a person fixing a record file by hand.
    It is not proof of authorship: ops are unsigned JSON, so an edit that
    also appends a matching op to the chain passes. Treat it as a
    consistency check between a record and its own log, not as tamper
    evidence; `git diff` remains the thing that shows a reader what changed.
    """
    prefix = f"{records_rel}/"
    if not offending.startswith(prefix):
        return False
    parts = offending[len(prefix) :].split("/")
    if len(parts) != 2:
        return False
    type_dir, filename = parts
    if not filename.endswith(RECORD_SUFFIX):
        return False
    record_id = filename[: -len(RECORD_SUFFIX)]
    path = store_root / "records" / type_dir / filename
    try:
        text = path.read_text()
    except OSError:
        return False
    try:
        record = load_record(text, path)
    except RecordFileError:
        return False
    if not isinstance(record, dict):
        return False
    if record.get("id") != record_id:
        return False
    record_type = record.get("record_type")
    if not isinstance(record_type, str):
        return False
    try:
        expected_type_dir = type_dir_name(record_type)
    except ValueError:
        return False
    if expected_type_dir != type_dir:
        return False
    chain_dir = store_root / "log" / type_dir / record_id
    return fold(read_ops(chain_dir)) == record


def validate_immutability(store_root: Path, errors: list[str]) -> None:
    """Fail on any store path that exists in git HEAD but was changed or removed
    in the working tree. Supersede is the only sanctioned mutation path, and it
    always writes a new record id -- so any in-place change to a path git already
    committed is a violation by construction, unless the op log accounts for it
    (see `_authorized_record_rewrite`). New, uncommitted paths are fine.

    History snapshots (`Store.archive_history`/`Store.iter_history`) are
    write-once, so a committed snapshot changing at all is a tamper by the same
    rule as a record file. `config.json` and `schemas/` change whenever
    `schemas sync` runs, so they are exempt.
    """
    if not store_root.exists():
        return
    repo_root = _git_toplevel(store_root)
    if repo_root is None:
        return
    if not _git_head_exists(repo_root):
        return
    try:
        rel = store_root.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return
    config_rel = (rel / "config.json").as_posix()
    schemas_rel = (rel / "schemas").as_posix() + "/"
    records_rel = (rel / "records").as_posix()
    result = _run_git(repo_root, "diff", "--name-status", "HEAD", "--", rel.as_posix())
    if result is None or result.returncode != 0:
        return
    for line in result.stdout.splitlines():
        line = line.rstrip("\n")
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("A"):
            continue
        offending = parts[1] if len(parts) > 1 else line
        if offending == config_rel or offending.startswith(schemas_rel):
            continue
        if not status.startswith("D") and _authorized_record_rewrite(
            store_root, records_rel, offending
        ):
            continue
        errors.append(
            f"immutability violation: committed store path modified or deleted "
            f"(git status {status}): {offending}"
        )


def load_records_for_validation(store_root: Path, errors: list[str]) -> list[dict[str, Any]]:
    records_dir = store_root / "records"
    if not records_dir.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(records_dir.rglob("*")):
        # Skipping these quietly would validate an unmigrated store as clean.
        if path.is_file() and path.suffix != RECORD_SUFFIX:
            errors.append(f"unrecognized record file (expected {RECORD_SUFFIX}): {path}")
    for path in sorted(records_dir.rglob(RECORD_GLOB)):
        try:
            record = load_record(path.read_text(), path)
        except RecordFileError as exc:
            errors.append(f"record malformed record file {path}: {exc}")
            continue
        if not isinstance(record, dict):
            errors.append(f"record file must be a record object: {path}")
            continue
        if record.get("revision") != compute_revision(record):
            errors.append(f"record revision tamper detected: {path}")
            continue
        records.append(record)
    return records
