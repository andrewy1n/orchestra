from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from orchestra.conductor.suite import SuitePolicy, SuiteStart, start_suite_background

PHASE = "migrate-call-sites"


def _worktree(tmp_path: Path) -> Path:
    work = tmp_path / "wt"
    work.mkdir()
    (work / "README").write_text("x\n")
    git = ["git", "-c", "user.email=t@example.com", "-c", "user.name=t"]
    for args in (["init"], ["add", "README"], ["commit", "-m", "init"]):
        subprocess.run([*git, *args], cwd=work, check=True, capture_output=True)
    return work


def _start(tmp_path: Path, work: Path, **kwargs: object) -> SuiteStart:
    started = start_suite_background(
        worktree=work,
        phase_slug=PHASE,
        log_dir=tmp_path / "logs",
        policy=SuitePolicy(mode="full", command="echo ok", gate="required"),
        **kwargs,  # pyright: ignore[reportArgumentType]
    )
    assert isinstance(started, SuiteStart)
    return started


def test_suite_start_accepts_injected_run(tmp_path: Path) -> None:
    work = _worktree(tmp_path)
    seen: list[tuple[list[str], Path, bool, bool, bool, float | None]] = []

    def run(
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | None,
        timeout: float | None,
        capture_output: bool,
        text: bool,
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str]:
        seen.append((list(argv), cwd, capture_output, text, check, timeout))
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    started = _start(tmp_path, work, runner=run)  # pyright: ignore[reportArgumentType]

    assert started.session_name.startswith("orchestra-suite-")
    assert len(seen) == 1
    argv, cwd, capture_output, text, check, timeout = seen[0]
    assert argv[:3] == ["tmux", "new-session", "-d"]
    assert cwd == work.resolve()
    assert (capture_output, text, check, timeout) == (True, True, False, None)


def test_suite_start_runs_tmux_through_command(tmp_path: Path) -> None:
    work = _worktree(tmp_path)

    def failing(
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | None,
        timeout: float | None,
        capture_output: bool,
        text: bool,
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 3, stdout="", stderr="no server\n")

    with pytest.raises(RuntimeError, match=r"^tmux exited 3: no server$"):
        _start(tmp_path, work, runner=failing)  # pyright: ignore[reportArgumentType]

    with pytest.raises(RuntimeError, match="tmux not found: no-such-tmux-binary"):
        _start(tmp_path, work, tmux="no-such-tmux-binary")


def test_suite_start_reports_non_missing_start_failure(tmp_path: Path) -> None:
    work = _worktree(tmp_path)

    def denied(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise PermissionError("denied")

    with pytest.raises(RuntimeError, match=r"^cannot run tmux: denied$"):
        _start(tmp_path, work, runner=denied)
