from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, overload

import pytest

from orchestra.tools import CliTool, Git, GitResult, ToolError, Version
from orchestra.tools.testing import scripted


class FakeGitRun:
    def __init__(
        self,
        returncode: int = 0,
        stdout: str | bytes = "",
        stderr: str = "",
        raises: BaseException | None = None,
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.raises = raises
        self.cwds: list[Path] = []
        self.argvs: list[list[str]] = []

    @overload
    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | None,
        timeout: float,
        capture_output: bool,
        text: Literal[True],
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str]: ...

    @overload
    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: bytes | None,
        timeout: float,
        capture_output: bool,
        text: Literal[False],
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[bytes]: ...

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | bytes | None,
        timeout: float,
        capture_output: bool,
        text: bool,
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
        if list(argv)[1:] == ["--version"]:
            if text:
                return subprocess.CompletedProcess(list(argv), 0, "git version 2.40.0\n", "")
            return subprocess.CompletedProcess(list(argv), 0, b"git version 2.40.0\n", b"")
        self.cwds.append(cwd)
        self.argvs.append(list(argv))
        if self.raises is not None:
            raise self.raises
        if text:
            out = self.stdout.decode() if isinstance(self.stdout, bytes) else self.stdout
            return subprocess.CompletedProcess(list(argv), self.returncode, out, self.stderr)
        raw = self.stdout.encode() if isinstance(self.stdout, str) else self.stdout
        return subprocess.CompletedProcess(list(argv), self.returncode, raw, self.stderr.encode())


def test_git_is_cli_tool_for_git() -> None:
    assert issubclass(Git, CliTool)
    assert Git.executable == "git"


def test_min_version_is_2_17() -> None:
    assert Git.min_version == Version(2, 17)


def test_runs_in_constructed_cwd(tmp_path: Path) -> None:
    fake = FakeGitRun(stdout="ok\n")
    Git(tmp_path, run=fake).run("status")
    assert fake.cwds == [tmp_path]


def test_run_returns_git_result(tmp_path: Path) -> None:
    fake = FakeGitRun(stdout="out", stderr="err")
    result = Git(tmp_path, run=fake).run("status")
    assert result == GitResult(0, "out", "err")
    assert fake.argvs == [["git", "status"]]


def test_run_does_not_raise_on_nonzero(tmp_path: Path) -> None:
    fake = FakeGitRun(returncode=128, stderr="fatal")
    result = Git(tmp_path, run=fake).run("status")
    assert result.returncode == 128
    assert result.stderr == "fatal"


def test_run_raises_tool_error_when_git_missing(tmp_path: Path) -> None:
    fake = FakeGitRun(raises=FileNotFoundError("git"))
    with pytest.raises(ToolError):
        Git(tmp_path, run=fake).run("status")


def test_run_raises_tool_error_on_timeout(tmp_path: Path) -> None:
    fake = FakeGitRun(raises=subprocess.TimeoutExpired(["git"], 1.0))
    with pytest.raises(ToolError) as info:
        Git(tmp_path, run=fake).run("status")
    assert "timed out" in str(info.value)


def test_text_returns_stripped_stdout(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "rev-parse", "HEAD"): "abc123\n"})
    assert Git(tmp_path, run=run).text("rev-parse", "HEAD") == "abc123"


def test_text_raises_on_nonzero(tmp_path: Path) -> None:
    fake = FakeGitRun(returncode=1, stderr="bad ref")
    with pytest.raises(ToolError) as info:
        Git(tmp_path, run=fake).text("rev-parse", "nope")
    assert info.value.returncode == 1
    assert info.value.stderr == "bad ref"


def test_show_bytes_returns_blob(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "show", "HEAD:a.bin"): b"\x00\xffdata"})
    assert Git(tmp_path, run=run).show_bytes("HEAD", "a.bin") == b"\x00\xffdata"


def test_show_bytes_missing_path_is_none(tmp_path: Path) -> None:
    fake = FakeGitRun(returncode=128, stderr="fatal: path missing")
    assert Git(tmp_path, run=fake).show_bytes("HEAD", "gone.txt") is None
