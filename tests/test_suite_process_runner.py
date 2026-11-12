from __future__ import annotations

import json
import os
import shlex
import shutil
import signal
import sys
import time
import uuid
from pathlib import Path

import pytest
from conftest import git, make_git_repo

from orchestra.cli import _build_parser
from orchestra.conductor import suite
from orchestra.conductor.suite import (
    SuitePolicy,
    SuiteResult,
    SuiteStart,
    poll_suite,
    start_suite_background,
)
from orchestra.tools import CliTool, ToolError


def _worktree(tmp_path: Path) -> tuple[Path, str]:
    worktree = make_git_repo()
    git(worktree, "config", "user.email", "suite-test@example.com")
    git(worktree, "config", "user.name", "suite test")
    marker = worktree / "tracked"
    marker.write_text("stable\n", encoding="utf-8")
    (worktree / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["unit"]\n\n'
        '[verify.unit]\nrunner = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]\n\n'
        '[suite]\nmode = "full"\ncommand = "true"\ngate = "required"\n',
        encoding="utf-8",
    )
    git(worktree, "add", "tracked")
    git(worktree, "add", "orchestra.toml")
    git(worktree, "commit", "-qm", "add tracked file")
    head = git(worktree, "rev-parse", "HEAD").stdout.strip()
    return worktree, head


def _start(worktree: Path, head: str, command: str, timeout: float | None = None) -> SuiteStart:
    arguments = {
        "worktree": worktree,
        "phase_slug": "suite-test",
        "phase_head": head,
        "session_name": "suite-test-job",
        "suite_command": command,
        "policy": SuitePolicy(mode="full", command=command, gate="required"),
        "allow_dirty": True,
    }
    started = (
        start_suite_background(**arguments)
        if timeout is None
        else start_suite_background(**arguments, timeout=timeout)
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


def _wait_result(started: SuiteStart, timeout: float = 8.0) -> SuiteResult:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = poll_suite(started)
        if result is not None:
            return result
        time.sleep(0.02)
    raise AssertionError("suite did not complete before the test deadline")


class PythonCli(CliTool):
    executable = sys.executable

    def invoke(self, *arguments: str) -> tuple[int, str, str]:
        log_path = self._cwd / ".suite" / f"cli-{uuid.uuid4().hex}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("wb") as output:
            process = self.start_process(
                [
                    sys.executable,
                    "-c",
                    "from orchestra.cli import main; raise SystemExit(main())",
                    *arguments,
                ],
                cwd=self._cwd,
                stdout=output,
                stderr=output,
            )
            try:
                returncode = process.wait(timeout=30)
            except ToolError:
                process.terminate_group()
                process.wait(timeout=2)
                raise
        return returncode, log_path.read_text(encoding="utf-8", errors="replace"), ""


class RunTracker:
    def __init__(self) -> None:
        self._runs: list[SuiteStart] = []

    def add(self, run: SuiteStart) -> None:
        self._runs.append(run)

    def close(self) -> None:
        for run in self._runs:
            if poll_suite(run) is None:
                suite.cancel_suite_run(run)
                _wait_result(run)


@pytest.fixture
def tracked_runs(request: pytest.FixtureRequest) -> RunTracker:
    tracker = RunTracker()
    request.addfinalizer(tracker.close)
    return tracker


def _cli_document(output: str) -> dict[str, object]:
    value: object = json.loads(output)
    assert isinstance(value, dict)
    return value


def _start_cli(worktree: Path, command: str, *options: str) -> dict[str, object]:
    code, output, error = PythonCli(worktree).invoke(
        "suite",
        "start",
        "--phase",
        "suite-test",
        "--session",
        "suite-cli-test",
        "--cwd",
        str(worktree),
        "--command",
        command,
        "--allow-dirty",
        *options,
    )
    assert code == 0, error
    return _cli_document(output)


def _poll_cli(
    worktree: Path,
    run_id: str,
    session_name: str = "suite-cli-test",
) -> tuple[int, dict[str, object]]:
    code, output, error = PythonCli(worktree).invoke(
        "suite",
        "poll",
        "--phase",
        "suite-test",
        "--session",
        session_name,
        "--cwd",
        str(worktree),
        "--run-id",
        run_id,
        "--allow-dirty",
    )
    assert code in (0, 1, 2, 3), error
    return code, _cli_document(output)


def _wait_cli_result(
    worktree: Path,
    run_id: str,
    timeout: float = 8.0,
    session_name: str = "suite-cli-test",
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        code, result = _poll_cli(worktree, run_id, session_name)
        if code != 3:
            return result
        time.sleep(0.05)
    raise AssertionError("suite CLI did not complete before the test deadline")


def test_starter_exits_while_background_command_continues(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / ".suite" / "release"
    marker.parent.mkdir(parents=True, exist_ok=True)
    command = f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done"

    started = _start(worktree, head, command)
    tracked_runs.add(started)

    assert started.run_id
    assert poll_suite(started) is None


def test_later_job_inspection_reads_the_persistent_run(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / ".suite" / "release"
    marker.parent.mkdir(parents=True, exist_ok=True)
    command = f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done"
    started = _start(worktree, head, command)
    tracked_runs.add(started)

    later = suite.load_suite_job(
        worktree=worktree,
        phase_slug="suite-test",
        session_name="suite-test-job",
    )

    assert later.run_id == started.run_id
    assert later.result_path == started.result_path
    _release(started, marker)


def test_collection_returns_combined_output_and_actual_exit_status(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / ".suite" / "release"
    marker.parent.mkdir(parents=True, exist_ok=True)
    command = (
        f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done; "
        "printf 'stdout value\\n'; printf 'stderr value\\n' >&2; exit 7"
    )
    started = _start(worktree, head, command)
    tracked_runs.add(started)
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


def test_revision_change_during_run_cannot_pass(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / ".suite" / "release"
    marker.parent.mkdir(parents=True, exist_ok=True)
    command = f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done"
    started = _start(worktree, head, command)
    tracked_runs.add(started)

    (worktree / "tracked").write_text("changed while running\n", encoding="utf-8")
    marker.touch()
    result = _wait_result(started)

    assert result.result == "blocked"
    assert result.reason == "revision_changed"


def test_record_refuses_pass_after_revision_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    worktree, head = _worktree(tmp_path)
    result = suite.SuiteResult(
        exit_code=0,
        duration_s=0.1,
        output="",
        output_sha256="",
        failing_node_ids=[],
        result="pass",
        revision=head,
        worktree=worktree,
        start_head=head,
    )
    monkeypatch.setattr(suite, "suite_worktree_matches", lambda *_args: False)

    with pytest.raises(RuntimeError, match="refusing passing check-run"):
        suite.record_suite_check_run(
            store_root=worktree,
            phase_slug="suite-test",
            effort="workflow-loop",
            suite=result,
        )


def test_duplicate_start_preserves_the_active_run(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / ".suite" / "release"
    marker.parent.mkdir(parents=True, exist_ok=True)
    command = f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done"
    started = _start(worktree, head, command)
    tracked_runs.add(started)
    assert started.request_path is not None
    assert started.run_dir is not None
    request_before = started.request_path.read_bytes()
    log_before = started.log_path.read_bytes()

    with pytest.raises(RuntimeError, match="active suite run"):
        _start(worktree, head, command)

    assert started.request_path.read_bytes() == request_before
    assert started.log_path.read_bytes() == log_before
    _release(started, marker)


def test_malformed_current_run_pointer_is_an_error(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / ".suite" / "release"
    marker.parent.mkdir(parents=True, exist_ok=True)
    command = f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done"
    started = _start(worktree, head, command)
    tracked_runs.add(started)
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


def test_worker_loss_is_reported_as_interrupted(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, head = _worktree(tmp_path)
    marker = worktree / ".suite" / "release"
    marker.parent.mkdir(parents=True, exist_ok=True)
    command = f"while [ ! -f {shlex.quote(str(marker))} ]; do sleep 0.02; done"
    started = _start(worktree, head, command)
    tracked_runs.add(started)
    assert started.ready_path is not None
    ready = suite.read_suite_json_object(started.ready_path)
    worker_pid = ready.get("worker_pid")
    assert isinstance(worker_pid, int)

    os.kill(worker_pid, signal.SIGKILL)
    result = _wait_result(started)

    assert result.result == "blocked"
    assert result.reason == "interrupted"
    marker.touch()


def test_timeout_stops_the_command_group(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, head = _worktree(tmp_path)
    child_pid = worktree / ".suite" / "child.pid"
    command = f"sleep 30 & echo $! > {shlex.quote(str(child_pid))}; wait"
    started = _start(worktree, head, command, timeout=0.2)
    tracked_runs.add(started)

    result = _wait_result(started)

    assert result.reason == "timeout"
    assert result.result == "blocked"
    assert result.duration_s < 8
    assert child_pid.is_file()


def test_cancellation_stops_only_the_selected_run(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, head = _worktree(tmp_path)
    command = "sleep 30 & wait"
    started = _start(worktree, head, command)
    tracked_runs.add(started)

    assert suite.cancel_suite_run(started) == "requested"
    result = _wait_result(started)

    assert result.reason == "cancelled"
    assert result.result == "blocked"
    assert suite.cancel_suite_run(started) == "cancelled"


def test_suite_cli_parses_timeout_run_selection_and_required_cancel_id() -> None:
    parser = _build_parser()
    start = parser.parse_args(["suite", "start", "--phase", "p1", "--timeout", "3.5"])
    poll = parser.parse_args(
        ["suite", "poll", "--phase", "p1", "--run-id", "9ecdad9be7e942e4aaf0fc7d9b0d3d5f"]
    )
    cancel = parser.parse_args(
        [
            "suite",
            "cancel",
            "--phase",
            "p1",
            "--run-id",
            "9ecdad9be7e942e4aaf0fc7d9b0d3d5f",
        ]
    )

    assert start.timeout == 3.5
    assert poll.run_id == cancel.run_id
    with pytest.raises(SystemExit):
        parser.parse_args(["suite", "cancel", "--phase", "p1"])


def test_cli_runs_a_suite_from_a_path_with_spaces(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, _head = _worktree(tmp_path)
    spaced_worktree = tmp_path / "work tree with spaces"
    worktree.rename(spaced_worktree)

    started = _start_cli(spaced_worktree, "printf 'cli path works\\n'")
    run_id_value = started.get("run_id")
    assert isinstance(run_id_value, str)
    run = suite.load_suite_job(
        worktree=spaced_worktree,
        phase_slug="suite-test",
        session_name="suite-cli-test",
        run_id=run_id_value,
    )
    tracked_runs.add(run)

    result = _wait_cli_result(spaced_worktree, run_id_value)

    assert result["state"] == "pass"
    assert run.log_path.read_text(encoding="utf-8") == "cli path works\n"


def test_cli_reports_command_failure_and_worker_startup_failure(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, _head = _worktree(tmp_path)
    failed = _start_cli(worktree, "printf 'failed command\\n'; exit 7")
    failed_id = failed.get("run_id")
    assert isinstance(failed_id, str)
    tracked_runs.add(
        suite.load_suite_job(
            worktree=worktree,
            phase_slug="suite-test",
            session_name="suite-cli-test",
            run_id=failed_id,
        )
    )
    failed_result = _wait_cli_result(worktree, failed_id)

    assert failed_result["state"] == "fail"
    assert failed_result["exit_code"] == 7

    git_path = shutil.which("git")
    assert git_path is not None
    tool_path = worktree / ".suite" / "startup-bin"
    tool_path.mkdir(parents=True)
    (tool_path / "git").symlink_to(git_path)
    environment = dict(os.environ)
    environment["PATH"] = str(tool_path)
    cli = PythonCli(worktree, env=environment)
    code, output, error = cli.invoke(
        "suite",
        "start",
        "--phase",
        "suite-test",
        "--session",
        "suite-cli-startup-failure",
        "--cwd",
        str(worktree),
        "--command",
        "true",
        "--allow-dirty",
    )
    assert code == 0, error
    startup = _cli_document(output)
    startup_id = startup.get("run_id")
    assert isinstance(startup_id, str)
    tracked_runs.add(
        suite.load_suite_job(
            worktree=worktree,
            phase_slug="suite-test",
            session_name="suite-cli-startup-failure",
            run_id=startup_id,
        )
    )

    startup_result = _wait_cli_result(
        worktree,
        startup_id,
        session_name="suite-cli-startup-failure",
    )

    assert startup_result["state"] == "blocked"
    assert startup_result["reason"] == "startup_failed"


def test_cli_cancellation_stops_a_child_process(
    tmp_path: Path,
    tracked_runs: RunTracker,
) -> None:
    worktree, _head = _worktree(tmp_path)
    run_dir = worktree / ".suite" / "child-control"
    run_dir.mkdir(parents=True)
    pid_path = run_dir / "child.pid"
    marker = run_dir / "child-finished"
    command = (
        f"(sleep 1; touch {shlex.quote(str(marker))}) & "
        f"echo $! > {shlex.quote(str(pid_path))}; wait"
    )
    started = _start_cli(worktree, command)
    run_id_value = started.get("run_id")
    assert isinstance(run_id_value, str)
    run = suite.load_suite_job(
        worktree=worktree,
        phase_slug="suite-test",
        session_name="suite-cli-test",
        run_id=run_id_value,
    )
    tracked_runs.add(run)

    deadline = time.monotonic() + 3
    while not pid_path.is_file() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert pid_path.is_file()

    code, output, error = PythonCli(worktree).invoke(
        "suite",
        "cancel",
        "--phase",
        "suite-test",
        "--session",
        "suite-cli-test",
        "--cwd",
        str(worktree),
        "--run-id",
        run_id_value,
    )
    assert code == 0, error
    assert _cli_document(output)["state"] == "requested"
    result = _wait_cli_result(worktree, run_id_value)
    time.sleep(1.1)

    assert result["reason"] == "cancelled"
    assert not marker.exists()
