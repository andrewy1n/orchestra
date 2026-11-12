from __future__ import annotations

import shlex
import time
from pathlib import Path

import pytest
from conftest import git, make_git_repo

from orchestra.conductor import suite
from orchestra.conductor.suite import (
    SuitePolicy,
    SuiteStart,
    poll_suite,
    start_suite_background,
)


def _worktree(tmp_path: Path) -> tuple[Path, str]:
    worktree = make_git_repo()
    git(worktree, "config", "user.email", "suite-test@example.com")
    git(worktree, "config", "user.name", "suite test")
    marker = worktree / "tracked"
    marker.write_text("stable\n", encoding="utf-8")
    git(worktree, "add", "tracked")
    git(worktree, "commit", "-qm", "add tracked file")
    head = git(worktree, "rev-parse", "HEAD").stdout.strip()
    return worktree, head


def _start(worktree: Path, head: str, command: str) -> SuiteStart:
    started = start_suite_background(
        worktree=worktree,
        phase_slug="suite-test",
        phase_head=head,
        session_name="suite-test-job",
        suite_command=command,
        policy=SuitePolicy(mode="full", command=command, gate="required"),
        allow_dirty=True,
    )
    assert isinstance(started, SuiteStart)
    return started


def _release(started: SuiteStart, marker: Path) -> None:
    marker.touch()
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        result = poll_suite(started)
        if result is not None:
            return
        time.sleep(0.02)
    raise AssertionError("suite did not complete before the test deadline")


def test_starter_exits_while_background_command_continues(tmp_path: Path) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / "release"
    command = f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done"

    started = _start(worktree, head, command)

    assert started.run_id
    assert poll_suite(started) is None


def test_later_job_inspection_reads_the_persistent_run(tmp_path: Path) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / "release"
    command = f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done"
    started = _start(worktree, head, command)

    later = suite.load_suite_job(
        worktree=worktree,
        phase_slug="suite-test",
        session_name="suite-test-job",
    )

    assert later.run_id == started.run_id
    assert later.result_path == started.result_path
    _release(started, marker)


def test_collection_returns_combined_output_and_actual_exit_status(tmp_path: Path) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / "release"
    command = (
        f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done; "
        "printf 'stdout value\\n'; printf 'stderr value\\n' >&2; exit 7"
    )
    started = _start(worktree, head, command)
    assert poll_suite(started) is None

    marker.touch()
    deadline = time.monotonic() + 5
    result = None
    while time.monotonic() < deadline and result is None:
        result = poll_suite(started)
        time.sleep(0.02)

    assert result is not None
    assert result.output == "stdout value\nstderr value\n"
    assert result.exit_code == 7
    assert result.result == "fail"


def test_duplicate_start_preserves_the_active_run(tmp_path: Path) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / "release"
    command = f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done"
    started = _start(worktree, head, command)
    assert started.request_path is not None
    assert started.run_dir is not None
    request_before = started.request_path.read_bytes()
    log_before = started.log_path.read_bytes()

    with pytest.raises(RuntimeError, match="active suite run"):
        _start(worktree, head, command)

    assert started.request_path.read_bytes() == request_before
    assert started.log_path.read_bytes() == log_before
    _release(started, marker)


def test_malformed_current_run_pointer_is_an_error(tmp_path: Path) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / "release"
    command = f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done"
    started = _start(worktree, head, command)
    assert started.run_dir is not None
    pointer = started.run_dir.parent.parent / "current.json"
    pointer.write_text("{", encoding="utf-8")

    with pytest.raises(RuntimeError, match="invalid suite run metadata"):
        suite.load_suite_job(
            worktree=worktree,
            phase_slug="suite-test",
            session_name="suite-test-job",
        )

    _release(started, marker)
