"""Independent acceptance contracts for lossless store transfer."""

from __future__ import annotations

import copy
import json
import os
import re
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

from orchestra.canon.backend import Backend, open_backend
from orchestra.canon.config import new_config
from orchestra.canon.oplog import append_resolved_op, fold, prune_before
from orchestra.canon.record_file import dump_record, load_record
from orchestra.canon.revision import compute_revision, with_revision
from orchestra.canon.store import Store

ROOT = Path(__file__).resolve().parents[2]


def _store(tmp_path: Path, name: str, selected: str = "sqlite") -> Backend:
    root = tmp_path / name / ".canon"
    root.mkdir(parents=True)
    (root / "store-binding.json").write_text('{"store":"local"}')
    config = {**new_config({"alpha": "0.1.0", "beta": "0.1.0"}), "backend": selected}
    backend = open_backend(root, config)
    for namespace in ("alpha", "beta"):
        backend.write_snapshot(
            namespace,
            json.dumps(
                {
                    "namespace": namespace,
                    "version": "0.1.0",
                    "types": {
                        "setting": {
                            "purpose": "A transfer fixture",
                            "lifecycle": "current",
                            "fields": {"title": {"type": "string"}},
                        }
                    },
                }
            ),
        )
    backend.write_config(config)
    return backend


def _root(backend: Backend) -> Path:
    if isinstance(backend, Store):
        return backend.root
    return Path(getattr(backend, "config_root"))


def _record(
    label: str, record_type: str = "alpha:setting", title: str = "first"
) -> dict[str, Any]:
    return with_revision(
        {
            "id": f"rec-{uuid.uuid5(uuid.NAMESPACE_URL, label)}",
            "record_type": record_type,
            "subject": label,
            "payload": {"title": title},
            "lifecycle_state": "active",
            "relationships": {},
            "recorded_at": "2026-02-03T04:05:06+00:00",
            "body": "A body with Unicode: café 🐙\n",
        }
    )


def _chain(
    backend: Backend, label: str, record_type: str = "alpha:setting", start: int = 1
) -> list[dict[str, Any]]:
    first = _record(label, record_type)
    last = with_revision({**first, "payload": {"title": "last"}, "body": "Changed\n"})
    ops: list[dict[str, Any]] = [
        {
            "seq": start,
            "op_id": label + "-first",
            "kind": "checkpoint" if start != 1 else "create",
            "outcome": "accepted",
            "record": first,
        },
        {
            "seq": start + 1,
            "op_id": label + "-rejected",
            "kind": "write",
            "outcome": "rejected_stale",
            "record": first,
            "expected_revision": "sha256:stale",
            "conflict_revision": first["revision"],
            "extra": {"list": [None, True, 7, "☃"]},
        },
        {
            "seq": start + 2,
            "op_id": label + "-last",
            "kind": "write",
            "outcome": "accepted",
            "record": last,
            "expected_revision": first["revision"],
            "extension": {"preserve": "exactly"},
        },
    ]
    for op in ops:
        backend.import_op(record_type, first["id"], op)
    backend.import_record(last)
    backend.archive_history(first)
    return ops


def _run(backend: Backend, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env.pop("CANON_STORE", None)
    env.pop("CANON_READONLY", None)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "orchestra.canon",
            "--root",
            str(_root(backend).parent),
            *args,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _export(backend: Backend, path: Path) -> list[dict[str, Any]]:
    result = _run(backend, "export", "--out", str(path))
    assert result.returncode == 0, (
        "canon export must succeed: " + result.stdout + result.stderr
    )
    assert path.is_file(), "canon export --out must write the requested file"
    return [json.loads(line) for line in path.read_text().splitlines()]


def _op(line: dict[str, Any]) -> dict[str, Any]:
    nested = line.get("op")
    return nested if isinstance(nested, dict) else line


def _key(line: dict[str, Any]) -> tuple[str, str, int]:
    assert isinstance(line.get("record_type"), str), (
        "Each JSONL line must name its record type"
    )
    assert isinstance(line.get("record_id"), str), (
        "Each JSONL line must name its record id"
    )
    assert isinstance(line.get("seq"), int), "Each JSONL line must name its seq"
    return line["record_type"], line["record_id"], line["seq"]


def _dump(path: Path, lines: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines)
    )


def _state(backend: Backend) -> str:
    with sqlite3.connect(_root(backend) / "canon.db") as connection:
        return "\n".join(connection.iterdump())


def _assert_import(backend: Backend, path: Path) -> None:
    result = _run(backend, "import", str(path))
    assert result.returncode == 0, (
        "canon import must succeed: " + result.stdout + result.stderr
    )


def _db_revisions(backend: Backend) -> dict[tuple[str, str], dict[str, Any]]:
    with sqlite3.connect(_root(backend) / "canon.db") as connection:
        return {
            (row[0], row[1]): json.loads(row[2])
            for row in connection.execute(
                "SELECT record_id, revision, record_json FROM revisions"
            )
        }


@pytest.mark.parametrize("selected", ["files", "sqlite"])
def test_export_one_json_line_per_op_in_canonical_order(
    tmp_path: Path, selected: str
) -> None:
    source = _store(tmp_path, "source", selected)
    expected: dict[tuple[str, str, int], dict[str, Any]] = {}
    for label, record_type in (
        ("zeta", "beta:setting"),
        ("omega", "alpha:setting"),
        ("alpha", "alpha:setting"),
    ):
        for op in _chain(source, label, record_type):
            expected[record_type, op["record"]["id"], op["seq"]] = op
    path = tmp_path / "export.jsonl"
    lines = _export(source, path)
    keys = [_key(line) for line in lines]
    assert len(lines) == len(expected), (
        "Export must contain one line for every accepted and rejected op"
    )
    assert keys == sorted(expected), (
        "Export must sort by record type, record id, then seq"
    )
    for line in lines:
        original = expected[_key(line)]
        exported = _op(line)
        assert {key: exported.get(key) for key in original} == original, (
            "Export must preserve every original op field"
        )


@pytest.mark.parametrize("selected", ["files", "sqlite"])
def test_two_exports_are_byte_identical(tmp_path: Path, selected: str) -> None:
    source = _store(tmp_path, "source", selected)
    _chain(source, "stable")
    first, second = tmp_path / "first.jsonl", tmp_path / "second.jsonl"
    _export(source, first)
    _export(source, second)
    assert first.read_bytes() == second.read_bytes()


def test_import_appends_unchanged_ops_and_materializes_fold_and_revisions(
    tmp_path: Path,
) -> None:
    source, target = _store(tmp_path, "source", "files"), _store(tmp_path, "target")
    original = _chain(source, "all-fields")
    path = tmp_path / "transfer.jsonl"
    _export(source, path)
    _assert_import(target, path)
    chains = list(target.iter_chains())
    assert chains == [(original[0]["record"]["id"], original)], (
        "Import must retain op content, order, rejected outcomes, and seq"
    )
    expected = fold(original)
    assert isinstance(expected, dict)
    assert target.read_record(expected["record_type"], expected["id"]) == expected
    with sqlite3.connect(_root(target) / "canon.db") as connection:
        rows = connection.execute(
            "SELECT record_id, revision, record_json FROM records"
        ).fetchall()
    assert [(row[0], row[1], json.loads(row[2])) for row in rows] == [
        (expected["id"], expected["revision"], expected)
    ]
    revisions = _db_revisions(target)
    for op in original:
        record = op["record"]
        assert revisions[record["id"], record["revision"]] == record


@pytest.mark.parametrize("occupied", ["record", "op", "history"])
def test_import_rejects_nonempty_store_without_writes(
    tmp_path: Path, occupied: str
) -> None:
    source, target = _store(tmp_path, "source", "files"), _store(tmp_path, "target")
    _chain(source, "incoming")
    record = _record("existing")
    if occupied == "record":
        target.import_record(record)
    elif occupied == "op":
        target.import_op(
            record["record_type"],
            record["id"],
            {
                "seq": 1,
                "op_id": "existing-op",
                "kind": "create",
                "outcome": "accepted",
                "record": record,
            },
        )
    else:
        target.archive_history(record)
    path = tmp_path / "transfer.jsonl"
    _export(source, path)
    before = _state(target)
    result = _run(target, "import", str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert _state(target) == before


@pytest.mark.parametrize("damage", ["gap", "hash", "malformed"])
def test_invalid_later_chain_rolls_back_entire_import(
    tmp_path: Path, damage: str
) -> None:
    source, target = _store(tmp_path, "source", "files"), _store(tmp_path, "target")
    _chain(source, "valid-first", "alpha:setting")
    bad = _chain(source, "invalid-later", "beta:setting")
    record_id = bad[0]["record"]["id"]
    path = tmp_path / "transfer.jsonl"
    lines = _export(source, path)
    damaged = [line for line in lines if _key(line)[1] == record_id]
    if damage == "gap":
        lines.remove(damaged[1])
    elif damage == "hash":
        _op(damaged[-1])["record"]["payload"]["title"] = "tampered without rehashing"
    _dump(path, lines)
    if damage == "malformed":
        with path.open("a") as handle:
            handle.write('{"incomplete":\n')
    before = _state(target)
    result = _run(target, "import", str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    output = result.stdout + result.stderr
    if damage != "malformed":
        assert record_id in output, (
            "Chain validation failure must name the offending record"
        )
    assert _state(target) == before, "A failed import must leave all tables unchanged"


@pytest.mark.parametrize("table", ["ops", "records", "revisions"])
def test_import_rolls_back_database_failure_after_valid_input(
    tmp_path: Path, table: str
) -> None:
    source, target = _store(tmp_path, "source", "files"), _store(tmp_path, "target")
    _chain(source, "sql-failure")
    path = tmp_path / "transfer.jsonl"
    _export(source, path)
    with sqlite3.connect(_root(target) / "canon.db") as connection:
        connection.execute(
            f"CREATE TRIGGER oracle_abort BEFORE INSERT ON {table} BEGIN SELECT RAISE(ABORT, 'oracle injected failure'); END"
        )
    before = _state(target)
    result = _run(target, "import", str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert _state(target) == before


def test_checkpoint_start_keeps_original_seq_and_op_fields(tmp_path: Path) -> None:
    source, target = _store(tmp_path, "source", "files"), _store(tmp_path, "target")
    original = _chain(source, "checkpoint", start=73)
    path = tmp_path / "transfer.jsonl"
    _export(source, path)
    _assert_import(target, path)
    assert list(target.iter_chains()) == [(original[0]["record"]["id"], original)]
    assert [op["seq"] for _, chain in target.iter_chains() for op in chain] == [
        73,
        74,
        75,
    ]


def test_database_export_import_export_is_byte_identical(tmp_path: Path) -> None:
    source, target = _store(tmp_path, "source"), _store(tmp_path, "target")
    _chain(source, "roundtrip-beta", "beta:setting")
    _chain(source, "roundtrip-alpha", start=17)
    first, second = tmp_path / "first.jsonl", tmp_path / "second.jsonl"
    _export(source, first)
    _assert_import(target, first)
    _export(target, second)
    assert first.read_bytes() == second.read_bytes()


def _pruned_source(tmp_path: Path) -> tuple[Backend, list[dict[str, Any]]]:
    source = _store(tmp_path, "pruned-source", "files")
    assert isinstance(source, Store)
    original = _chain(source, "pruned")
    snapshots = list(source.read_history())
    current = original[-1]["record"]
    chain_dir = source.log_dir / "alpha__setting" / current["id"]
    checkpoint = append_resolved_op(
        chain_dir, "checkpoint", lambda state: ("accepted", state, {})
    )
    prune_before(chain_dir, checkpoint["seq"])
    surviving = list(source.iter_chains())
    assert len(surviving) == 1 and surviving[0][1][0]["kind"] == "checkpoint"
    retained_hashes = {
        op["record"]["revision"] for _, chain in surviving for op in chain
    }
    assert any(record["revision"] not in retained_hashes for record in snapshots), (
        "Fixture must include archived revisions absent from surviving ops"
    )
    return source, snapshots


def test_import_preserves_retained_history_absent_from_checkpoint_ops(
    tmp_path: Path,
) -> None:
    source, history = _pruned_source(tmp_path)
    target = _store(tmp_path, "target")
    path = tmp_path / "retained-history.jsonl"
    _export(source, path)
    _assert_import(target, path)
    for record in source.iter_records():
        imported = target.read_record(record["record_type"], record["id"])
        assert imported["revision"] == compute_revision(record) == record["revision"]
    revisions = _db_revisions(target)
    for snapshot in history:
        assert revisions.get((snapshot["id"], snapshot["revision"])) == snapshot, (
            "Retained history must survive even after its ops have been pruned"
        )


def _verify(source: Backend) -> subprocess.CompletedProcess[str]:
    script = ROOT / "scripts" / "verify_import.py"
    assert script.is_file(), (
        "scripts/verify_import.py must provide the import verification entrypoint"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env.pop("CANON_STORE", None)
    env.pop("CANON_READONLY", None)
    return subprocess.run(
        [sys.executable, str(script), str(_root(source))],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_counts(output: str, records: int, mismatches: int) -> None:
    assert re.search(
        rf"\b{records}\s+records?\b|\brecords?\s*[:=]\s*{records}\b",
        output,
        re.IGNORECASE,
    ), output
    assert re.search(
        rf"\b{mismatches}\s+mismatches?\b|\bmismatches?\s*[:=]\s*{mismatches}\b",
        output,
        re.IGNORECASE,
    ), output


def test_verify_import_script_succeeds_and_counts_checkpoint_history(
    tmp_path: Path,
) -> None:
    source, _ = _pruned_source(tmp_path)
    result = _verify(source)
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_counts(result.stdout + result.stderr, 1, 0)


@pytest.mark.parametrize("seed", ["record", "history"])
def test_verify_import_script_fails_for_seeded_snapshot_mismatch(
    tmp_path: Path, seed: str
) -> None:
    source, history = _pruned_source(tmp_path)
    assert isinstance(source, Store)
    record = next(source.iter_records()) if seed == "record" else history[0]
    path = (
        source.record_path(record["record_type"], record["id"])
        if seed == "record"
        else source.history_snapshot_path(
            record["record_type"], record["id"], record["revision"]
        )
    )
    changed = copy.deepcopy(load_record(path.read_text(), path))
    changed["body"] = "A seeded mismatch that does not match the revision hash\n"
    path.write_text(dump_record(changed))
    result = _verify(source)
    assert result.returncode == 1, result.stdout + result.stderr
    output = result.stdout + result.stderr
    assert re.search(
        r"\b1\s+records?\b|\brecords?\s*[:=]\s*1\b", output, re.IGNORECASE
    ), output
    count = re.search(
        r"\b([1-9][0-9]*)\s+mismatches?\b|\bmismatches?\s*[:=]\s*([1-9][0-9]*)\b",
        output,
        re.IGNORECASE,
    )
    assert count, "A seeded mismatch must report a positive mismatch count: " + output
