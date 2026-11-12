from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from dashboard.backend.server import service
from dashboard.backend.snapshot import Snapshot
from orchestra.canon.project import Project, open_store


class ScheduledLock:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.follower_attempted = threading.Event()

    def __enter__(self) -> ScheduledLock:
        if threading.current_thread().name.startswith("follower"):
            self.follower_attempted.set()
        self.lock.acquire()
        return self

    def __exit__(self, *_args: object) -> None:
        self.lock.release()


def _add_effort(target: Project, subject: str) -> None:
    target.create(
        record_type="score:effort",
        subject=subject,
        payload={"goal": subject, "kind": "deliver"},
    )


def _reader(store: Path) -> service.Reader:
    target = open_store(store)
    _add_effort(target, "alpha")
    return service.Reader(target)


def test_concurrent_snapshot_requests_share_one_build(
    store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = _reader(store)
    original = service.load_snapshot
    started = threading.Event()
    follower_started = threading.Event()
    calls: list[str] = []

    def load(target: Project, token: str) -> Snapshot:
        calls.append(token)
        if threading.current_thread().name.startswith("leader"):
            started.set()
            assert follower_started.wait(10)
        return original(target, token=token)

    monkeypatch.setattr(service, "load_snapshot", load)
    with (
        ThreadPoolExecutor(max_workers=1, thread_name_prefix="leader") as leader,
        ThreadPoolExecutor(max_workers=1, thread_name_prefix="follower") as follower,
    ):
        first = leader.submit(reader.cache.current)
        assert started.wait(10)

        def follow() -> Snapshot:
            follower_started.set()
            return reader.cache.current()

        second = follower.submit(follow)
        first_snapshot = first.result(timeout=15)
        second_snapshot = second.result(timeout=15)
    assert len(calls) == 1
    assert first_snapshot is second_snapshot
    assert reader.hub().generated_at is not None
    assert len(calls) == 1


def test_queued_snapshot_request_reads_the_current_generation(
    store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = _reader(store)
    reader.snapshot()
    scheduled = ScheduledLock()
    monkeypatch.setattr(reader.cache, "lock", scheduled)
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="follower") as pool:
        with scheduled:
            pending = pool.submit(reader.snapshot)
            assert scheduled.follower_attempted.wait(10)
            _add_effort(reader.target, "beta")
        snapshot = pending.result(timeout=15)
    assert {effort.effort for effort in snapshot.efforts} == {"alpha", "beta"}
    assert snapshot.token == reader.target.change_token()


def test_queued_token_poll_reads_the_current_generation(
    store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = _reader(store)
    reader.snapshot()
    scheduled = ScheduledLock()
    monkeypatch.setattr(reader.cache, "lock", scheduled)
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="follower") as pool:
        with scheduled:
            pending = pool.submit(reader.token)
            assert scheduled.follower_attempted.wait(10)
            _add_effort(reader.target, "beta")
        token = pending.result(timeout=15)
    assert token.token == reader.target.change_token()
    assert {effort.effort for effort in reader.snapshot().efforts} == {"alpha", "beta"}


def test_drop_during_a_build_does_not_restore_the_invalidated_snapshot(
    store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = _reader(store)
    original = service.load_snapshot
    started = threading.Event()
    follower_started = threading.Event()
    calls: list[str] = []

    def load(target: Project, token: str) -> Snapshot:
        calls.append(token)
        if threading.current_thread().name.startswith("leader"):
            started.set()
            assert follower_started.wait(10)
        return original(target, token=token)

    monkeypatch.setattr(service, "load_snapshot", load)
    with (
        ThreadPoolExecutor(max_workers=1, thread_name_prefix="leader") as leader,
        ThreadPoolExecutor(max_workers=1, thread_name_prefix="follower") as follower,
    ):
        first = leader.submit(reader.cache.current)
        assert started.wait(10)

        def drop() -> None:
            follower_started.set()
            reader.cache.drop()

        invalidation = follower.submit(drop)
        invalidated = first.result(timeout=15)
        invalidation.result(timeout=15)
    fresh = reader.cache.current()
    assert fresh is not invalidated
    assert len(calls) == 2


def test_failed_snapshot_build_releases_waiters_for_a_retry(
    store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = _reader(store)
    original = service.load_snapshot
    calls = 0

    def load(target: Project, token: str) -> Snapshot:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise service.store.ModelError("read failed")
        return original(target, token=token)

    monkeypatch.setattr(service, "load_snapshot", load)
    with pytest.raises(service.store.ModelError, match="read failed"):
        reader.snapshot()
    with ThreadPoolExecutor(max_workers=1) as pool:
        snapshot = pool.submit(reader.snapshot).result(timeout=15)
    assert [effort.effort for effort in snapshot.efforts] == ["alpha"]
    assert calls == 2


def test_token_poll_completes_while_snapshot_construction_is_blocked(
    store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = _reader(store)
    original = service.load_snapshot
    started, release, polled = threading.Event(), threading.Event(), threading.Event()

    def load(target: Project, token: str) -> Snapshot:
        started.set()
        assert release.wait(10)
        return original(target, token=token)

    def poll() -> str:
        token = reader.token().token
        polled.set()
        return token

    monkeypatch.setattr(service, "load_snapshot", load)
    with ThreadPoolExecutor(max_workers=2) as pool:
        snapshot = pool.submit(reader.snapshot)
        assert started.wait(10)
        token = pool.submit(poll)
        try:
            assert polled.wait(3), "Token polling waits for snapshot construction"
        finally:
            release.set()
        assert token.result(timeout=10) == reader.target.change_token()
        snapshot.result(timeout=10)


def test_completed_build_does_not_republish_after_invalidation(
    store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = _reader(store)
    original = service.load_snapshot
    built, release, dropped = threading.Event(), threading.Event(), threading.Event()

    def load(target: Project, token: str) -> Snapshot:
        result = original(target, token=token)
        built.set()
        assert release.wait(10)
        return result

    def drop() -> None:
        reader.cache.drop()
        dropped.set()

    monkeypatch.setattr(service, "load_snapshot", load)
    with ThreadPoolExecutor(max_workers=2) as pool:
        building = pool.submit(reader.cache.current)
        assert built.wait(10)
        invalidating = pool.submit(drop)
        try:
            assert dropped.wait(3)
        finally:
            release.set()
        old = building.result(timeout=10)
        invalidating.result(timeout=10)
    assert reader.cache.snapshot is None
    assert reader.cache.current() is not old
