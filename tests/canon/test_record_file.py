from __future__ import annotations

import json
import multiprocessing
import time
from pathlib import Path

import pytest

from orchestra.canon.record_file import RecordFileError, dump_record, load_record, normalize_body, prepare_record
from orchestra.canon.revision import compute_revision, with_revision
from orchestra.canon.store import Store, StoreLockError


def sample_record(**overrides) -> dict:
    record = {
        "id": "rec-00000000-0000-4000-8000-000000000001",
        "record_type": "ns:kind",
        "subject": "subject",
        "payload": {"scope": "x"},
        "lifecycle_state": "active",
        "relationships": {},
        "recorded_at": "2026-01-01T00:00:00+00:00",
        "revision": "",
        "body": "",
    }
    record.update(overrides)
    return record


def test_body_normalization():
    assert normalize_body("") == ""
    assert normalize_body("line one  \nline two\t\n") == "line one\nline two\n"
    assert normalize_body("\n\nline one\nline two\n\n\n") == "line one\nline two\n"
    assert normalize_body("\n   \n\t\n") == ""


@pytest.mark.parametrize("body", ["", "hello world\n"])
def test_round_trip(body):
    record = with_revision(prepare_record(sample_record(body=body)))
    assert load_record(dump_record(record), "test-path") == record


def test_body_with_fence_lines_and_code_blocks_does_not_break_parsing():
    body = "intro\n\n---\n\n```python\nprint('hi')\nx = {'a': 1}\n```\n\ntrailing line with --- inline\n"
    record = with_revision(prepare_record(sample_record(body=body)))
    loaded = load_record(dump_record(record), "test-path")
    assert loaded["body"] == body
    assert loaded == record


def test_exact_file_layout():
    record = with_revision(prepare_record(sample_record(body="a line\n")))
    frontmatter = {k: v for k, v in record.items() if k != "body"}
    expected = "---\n" + json.dumps(frontmatter, sort_keys=True, indent=2) + "\n---\n\na line\n"
    assert dump_record(record) == expected


@pytest.mark.parametrize(
    "text",
    ["no fence here\n---\n\nbody\n", "---\n{not valid json\n---\n\nbody\n", "---\n{}\nbody without a closing fence\n"],
)
def test_malformed_files_name_their_path(text):
    with pytest.raises(RecordFileError, match="/tmp/bad.md"):
        load_record(text, "/tmp/bad.md")


def test_revision_stable_across_write_read_cycle(tmp_path):
    store = Store(tmp_path / "store")
    stored = store.create_record(sample_record(body="a body line\nwith two lines\n"))
    reloaded = store.read_record("ns:kind", stored["id"])
    assert reloaded == stored
    assert reloaded["revision"] == compute_revision(reloaded)


def test_revision_unchanged_by_frontmatter_reformatting(tmp_path):
    store = Store(tmp_path / "store")
    stored = store.create_record(sample_record(body="unchanged body\n"))
    path = store.record_path("ns:kind", stored["id"])
    frontmatter = {k: v for k, v in stored.items() if k != "body"}
    reformatted = f"---\n{json.dumps(frontmatter, indent=4)}\n---\n\n{stored['body']}"
    assert reformatted != path.read_text()
    path.write_text(reformatted)
    assert store.read_record("ns:kind", stored["id"]) == stored


def test_body_is_normalized_before_hashing(tmp_path):
    store = Store(tmp_path / "store")
    stored = store.create_record(sample_record(body="\n\nline with trailing space   \n\n\n"))
    assert stored["body"] == "line with trailing space\n"
    assert stored["revision"] == compute_revision(stored)


def test_tampered_record_is_detected(tmp_path):
    store = Store(tmp_path / "store")
    stored = store.create_record(sample_record())
    path = store.record_path("ns:kind", stored["id"])
    path.write_text(path.read_text().replace('"subject"', '"subject_x"'))
    from orchestra.canon.store import StoreError

    with pytest.raises(StoreError, match="tamper"):
        store.read_record("ns:kind", stored["id"])


def hold_write_lock(store_root: str, hold_seconds: float, ready_path: str) -> None:
    with Store(Path(store_root)).write_lock():
        Path(ready_path).write_text("ready")
        time.sleep(hold_seconds)


def test_second_writer_fails_fast_while_first_holds_the_lock(tmp_path):
    root = tmp_path / "store"
    root.mkdir()
    ready = root / "ready.marker"
    holder = multiprocessing.get_context("fork").Process(
        target=hold_write_lock, args=(str(root), 3.0, str(ready))
    )
    holder.start()
    try:
        deadline = time.monotonic() + 5.0
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.exists()
        store = Store(root)
        start = time.monotonic()
        with pytest.raises(StoreLockError) as caught:
            with store.write_lock():
                pass
        assert time.monotonic() - start < 3.0
        assert str(store.lock_path()) in str(caught.value)
        assert str(holder.pid) in str(caught.value)
    finally:
        holder.join(timeout=5)
        if holder.is_alive():
            holder.terminate()
            holder.join(timeout=5)


def test_lock_can_be_reacquired_after_release(tmp_path):
    store = Store(tmp_path / "store")
    with store.write_lock():
        pass
    with store.write_lock():
        pass
    assert not store.lock_path().exists()
