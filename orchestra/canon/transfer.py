"""Deterministic operation envelopes and atomic SQLite store import."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import TextIO

from orchestra.canon.backend import Backend
from orchestra.canon.errors import StoreError
from orchestra.canon.oplog import fold
from orchestra.canon.paths import validate_record_id, validate_record_type
from orchestra.canon.revision import compute_revision
from orchestra.canon.sqlite_backend import SqliteBackend
from orchestra.canon.types import JsonValue, Record, StoredOp


def export_ops(backend: Backend, out: TextIO) -> int:
    history: dict[tuple[str, str], list[Record]] = defaultdict(list)
    for snapshot in backend.read_history():
        history[snapshot["record_type"], snapshot["id"]].append(snapshot)
    chains: list[tuple[str, str, list[StoredOp]]] = []
    for record_id, ops in backend.iter_chains():
        record_type = next((op["record"]["record_type"] for op in ops if op["record"]), None)
        if record_type is None:
            raise StoreError(f"{record_id}: cannot determine chain record type")
        chains.append((record_type, record_id, ops))
    count = 0
    for record_type, record_id, ops in sorted(chains):
        snapshots = history.pop((record_type, record_id), [])
        for index, op in enumerate(sorted(ops, key=lambda op: op["seq"])):
            envelope: dict[str, object] = {
                "record_type": record_type,
                "record_id": record_id,
                "seq": op["seq"],
                "op": op,
            }
            if index == 0:
                envelope["history"] = sorted(snapshots, key=lambda record: record["revision"])
            out.write(
                json.dumps(
                    envelope,
                    sort_keys=True,
                    ensure_ascii=False,
                    allow_nan=False,
                    separators=(",", ":"),
                )
                + "\n"
            )
            count += 1
    if history:
        record_type, record_id = sorted(history)[0]
        raise StoreError(f"{record_type}/{record_id}: retained history has no op chain")
    return count


def _snapshot(value: JsonValue, record_type: str, record_id: str) -> Record:
    if not isinstance(value, dict):
        raise StoreError(f"{record_id}: snapshot must be an object")
    if value.get("id") != record_id or value.get("record_type") != record_type:
        raise StoreError(f"{record_id}: snapshot identity mismatch")
    if value.get("revision") != compute_revision(value):
        raise StoreError(f"{record_id}: snapshot revision hash mismatch")
    for key in ("subject", "lifecycle_state", "recorded_at"):
        if not isinstance(value.get(key), str):
            raise StoreError(f"{record_id}: snapshot {key} must be a string")
    return value  # pyright: ignore[reportReturnType]  # Replay retains legacy envelope fields for later store validation.


def _restore(
    backend: Backend,
    record_type: str,
    record_id: str,
    ops: list[StoredOp],
    history: list[Record],
) -> None:
    revisions: dict[str, Record] = {}
    for op in ops:
        backend.import_op(record_type, record_id, op)
        if op["outcome"] == "accepted" and op["record"] is not None:
            revisions[op["record"]["revision"]] = op["record"]
    for record in revisions.values():
        backend.archive_history(record)
        backend.delete_history_snapshot(record_type, record_id, record["revision"])
    current = fold(ops)
    if current is not None:
        backend.import_record(current)
    for record in history:
        backend.archive_history(record)


def _invalid_constant(value: str) -> object:
    raise ValueError(f"invalid JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def import_ops(backend: Backend, src: TextIO) -> int:
    if not isinstance(backend, SqliteBackend):
        raise StoreError("import requires a SQLite store")
    count = 0
    key: tuple[str, str] | None = None
    seen_ids: set[str] = set()
    ops: list[StoredOp] = []
    history: list[Record] = []
    with backend.transaction():
        if not backend.is_empty():
            raise StoreError("import requires an empty store")
        for line_no, line in enumerate(src, start=1):
            envelope: JsonValue = None
            try:
                envelope = json.loads(
                    line,
                    parse_constant=_invalid_constant,
                    object_pairs_hook=_unique_object,
                )
                if not isinstance(envelope, dict):
                    raise ValueError("envelope must be an object")
                if set(envelope) - {"record_type", "record_id", "seq", "op", "history"}:
                    raise ValueError("unknown envelope metadata")
                raw_type, raw_id = envelope["record_type"], envelope["record_id"]
                record_type, record_id = raw_type, raw_id
                if not isinstance(record_type, str) or not isinstance(record_id, str):
                    raise ValueError("record identity must contain strings")
                validate_record_type(record_type)
                validate_record_id(record_id)
                next_key = (record_type, record_id)
                if key != next_key:
                    if key is not None:
                        _restore(backend, *key, ops, history)
                        if next_key <= key:
                            raise StoreError(f"{record_id}: chain order or duplicate chain")
                    if record_id in seen_ids:
                        raise StoreError(f"{record_id}: duplicate record identity")
                    seen_ids.add(record_id)
                    key, ops, history = next_key, [], []
                raw_op = envelope["op"]
                seq = envelope["seq"]
                if (
                    not isinstance(raw_op, dict)
                    or type(seq) is not int
                    or seq < 1
                    or type(raw_op.get("seq")) is not int
                    or raw_op.get("seq") != seq
                ):
                    raise StoreError(f"{record_id}: invalid op or seq")
                op_value = raw_op
                if ops and seq != ops[-1]["seq"] + 1:
                    raise StoreError(f"{record_id}: sequence gap or duplicate at {seq}")
                if not ops and seq != 1 and op_value.get("kind") != "checkpoint":
                    raise StoreError(f"{record_id}: sequence must start at 1 or a checkpoint")
                if (
                    not isinstance(op_value.get("op_id"), str)
                    or not isinstance(op_value.get("kind"), str)
                    or not isinstance(op_value.get("outcome"), str)
                    or "record" not in op_value
                ):
                    raise StoreError(f"{record_id}: malformed op")
                if op_value["record"] is not None:
                    _snapshot(op_value["record"], record_type, record_id)
                op: StoredOp = op_value  # pyright: ignore[reportAssignmentType]  # Replay retains legacy operation fields for later store validation.
                if "history" in envelope:
                    raw_history = envelope["history"]
                    if ops or not isinstance(raw_history, list):
                        raise StoreError(
                            f"{record_id}: history metadata belongs on the first envelope"
                        )
                    history = [_snapshot(value, record_type, record_id) for value in raw_history]
                    if len({record["revision"] for record in history}) != len(history):
                        raise StoreError(f"{record_id}: duplicate history revision")
                ops.append(op)
                count += 1
            except (ValueError, KeyError, TypeError) as exc:
                identity = f" {envelope.get('record_id', '')}" if isinstance(envelope, dict) else ""
                raise StoreError(f"import line {line_no}{identity}: {exc}") from exc
        if key is not None:
            _restore(backend, *key, ops, history)
    return count
