from __future__ import annotations

import multiprocessing
import random
import time
from pathlib import Path

import pytest

from orchestra.canon import oplog
from orchestra.canon.store import CHECKPOINT_THRESHOLD, StaleWriteError, Store, StoreError

RECORD_TYPE = "ns:kind"


def base_record(record_id: str, subject: str, counter: int = 0) -> dict:
    return {
        "id": record_id,
        "record_type": RECORD_TYPE,
        "subject": subject,
        "payload": {"counter": counter},
        "lifecycle_state": "active",
        "relationships": {},
        "recorded_at": "2026-01-01T00:00:00+00:00",
        "revision": "",
    }


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "store")


def test_create_appends_one_op_and_materializes(store):
    record_id = store.new_id()
    stored = store.create_record(base_record(record_id, "s1"))
    ops = oplog.read_ops(store._chain_dir(RECORD_TYPE, record_id))
    assert [op["kind"] for op in ops] == ["create"]
    assert store.read_record(RECORD_TYPE, record_id)["revision"] == stored["revision"]


def test_second_create_over_same_id_is_rejected_and_does_not_overwrite(store):
    record_id = store.new_id()
    store.create_record(base_record(record_id, "s1"))
    with pytest.raises(StoreError):
        store.create_record(base_record(record_id, "s2"))
    assert store.read_record(RECORD_TYPE, record_id)["subject"] == "s1"


def test_write_without_expected_revision_over_a_live_record_is_rejected(store):
    stored = store.create_record(base_record(store.new_id(), "s1"))
    with pytest.raises(StoreError, match="expected revision required"):
        store.write_record(dict(stored, subject="s2"))


def test_stale_expected_revision_is_rejected_and_leaves_state_unchanged(store):
    stored = store.create_record(base_record(store.new_id(), "s1"))
    with pytest.raises(StaleWriteError):
        store.write_record(dict(stored, subject="s2"), expected_revision="sha256:dead")
    assert store.read_record(RECORD_TYPE, stored["id"])["subject"] == "s1"


def test_orphan_temp_file_is_ignored_by_fold(store):
    record_id = store.new_id()
    store.create_record(base_record(record_id, "s1"))
    chain_dir = store._chain_dir(RECORD_TYPE, record_id)
    (chain_dir / ".tmp-orphan").write_text('{"kind": "write"}')
    assert [op["kind"] for op in oplog.read_ops(chain_dir)] == ["create"]


def test_checkpoint_bounds_chain_length_and_preserves_state(store):
    stored = store.create_record(base_record(store.new_id(), "s1"))
    for i in range(1, CHECKPOINT_THRESHOLD + 5):
        stored = store.write_record(
            dict(stored, payload={"counter": i}), expected_revision=stored["revision"]
        )
    remaining = oplog.read_ops(store._chain_dir(RECORD_TYPE, stored["id"]))
    assert len(remaining) < CHECKPOINT_THRESHOLD + 5
    assert any(op["kind"] == "checkpoint" for op in remaining)
    on_disk = store.read_record(RECORD_TYPE, stored["id"])
    assert on_disk["payload"]["counter"] == CHECKPOINT_THRESHOLD + 4
    assert on_disk["revision"] == stored["revision"]


def test_delete_record_file_purges_the_chain(store):
    record_id = store.new_id()
    store.create_record(base_record(record_id, "s1"))
    chain_dir = store._chain_dir(RECORD_TYPE, record_id)
    store.delete_record_file(RECORD_TYPE, record_id)
    assert not chain_dir.exists()
    assert not store.record_exists(RECORD_TYPE, record_id)


def test_history_snapshot_is_written_once_and_is_idempotent(store):
    stored = store.create_record(base_record(store.new_id(), "s1"))
    store.archive_history(stored)
    store.archive_history(stored)
    path = store.history_snapshot_path(RECORD_TYPE, stored["id"], stored["revision"])
    assert path.is_file()
    path.write_text(path.read_text() + "x")
    with pytest.raises(StoreError, match="history snapshot conflict"):
        store.archive_history(stored)


def test_write_archives_the_prior_revision_only_when_a_record_existed(store):
    stored = store.create_record(base_record(store.new_id(), "s1"))
    updated = store.write_record(
        dict(stored, payload={"counter": 1}),
        expected_revision=stored["revision"],
        archive_prior=stored,
    )
    assert store.history_snapshot_path(RECORD_TYPE, stored["id"], stored["revision"]).is_file()
    assert not store.history_snapshot_path(RECORD_TYPE, stored["id"], updated["revision"]).exists()


def concurrent_create(store_root: str, record_id: str, subject: str) -> str:
    try:
        Store(Path(store_root)).create_record(base_record(record_id, subject))
        return "created"
    except StoreError:
        return "rejected"


def concurrent_increment(store_root: str, record_id: str, attempts: int) -> int:
    store = Store(Path(store_root))
    landed = 0
    for _ in range(attempts):
        for retry in range(300):
            current = store.read_record(RECORD_TYPE, record_id)
            proposed = dict(current, payload={"counter": current["payload"]["counter"] + 1})
            try:
                store.write_record(proposed, expected_revision=current["revision"])
                landed += 1
                break
            except StaleWriteError:
                if retry > 10:
                    time.sleep(random.uniform(0, 0.002))
        else:
            raise AssertionError("writer starved after 300 retries")
    return landed


def test_concurrent_creates_to_distinct_ids_all_survive(store):
    ids = [store.new_id() for _ in range(8)]
    with multiprocessing.get_context("spawn").Pool(processes=8) as pool:
        results = pool.starmap(
            concurrent_create, [(str(store.root), rid, f"subject-{i}") for i, rid in enumerate(ids)]
        )
    assert results == ["created"] * 8
    assert {r["id"] for r in store.iter_records(RECORD_TYPE)} == set(ids)


def test_concurrent_creates_to_the_same_id_let_exactly_one_win(store):
    record_id = store.new_id()
    with multiprocessing.get_context("spawn").Pool(processes=6) as pool:
        results = pool.starmap(
            concurrent_create, [(str(store.root), record_id, f"subject-{i}") for i in range(6)]
        )
    assert results.count("created") == 1
    assert results.count("rejected") == 5
    assert len(oplog.read_ops(store._chain_dir(RECORD_TYPE, record_id))) == 6


def test_concurrent_optimistic_writers_lose_no_increments(store):
    stored = store.create_record(base_record(store.new_id(), "s1"))
    writers, attempts = 5, 4
    with multiprocessing.get_context("spawn").Pool(processes=writers) as pool:
        landed = pool.starmap(
            concurrent_increment, [(str(store.root), stored["id"], attempts)] * writers
        )
    assert sum(landed) == writers * attempts
    assert store.read_record(RECORD_TYPE, stored["id"])["payload"]["counter"] == writers * attempts
