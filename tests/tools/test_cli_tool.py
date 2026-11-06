from __future__ import annotations

import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar, Literal, overload

import pytest

from orchestra.tools.cli_tool import CliTool, run_subprocess
from orchestra.tools.errors import ToolError


class FakeRun:
    def __init__(
        self,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
        raises: BaseException | None = None,
        version_returncode: int = 0,
    ) -> None:
        self.version_returncode = version_returncode
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.raises = raises
        self.argv: list[str] = []
        self.kwargs: dict[str, object] = {}
        self.calls: list[dict[str, object]] = []

    @overload
    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | None,
        timeout: float | None,
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
        timeout: float | None,
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
        timeout: float | None,
        capture_output: bool,
        text: bool,
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
        if list(argv)[1:] == ["--version"]:
            return subprocess.CompletedProcess(
                list(argv), self.version_returncode, f"{argv[0]} version 1.0.0\n", ""
            )
        self.argv = list(argv)
        self.kwargs = {
            "cwd": cwd,
            "input": input,
            "timeout": timeout,
            "capture_output": capture_output,
            "text": text,
            "check": check,
            "env": env,
        }
        self.calls.append(self.kwargs)
        if self.raises is not None:
            raise self.raises
        if not text:
            return subprocess.CompletedProcess(
                list(argv), self.returncode, self.stdout.encode(), self.stderr.encode()
            )
        return subprocess.CompletedProcess(list(argv), self.returncode, self.stdout, self.stderr)


class FakeTool(CliTool):
    executable: ClassVar[str] = "faketool"

    def text(self, *args: str, input: str | None = None) -> str:
        return self._text(*args, input=input)

    def raw(self, *args: str, input: bytes | None = None) -> bytes:
        return self._execute_bytes(args, input).stdout

    def json(self, *args: str) -> object:
        return self._json(*args)


class PythonTool(CliTool):
    executable: ClassVar[str] = sys.executable

    def text(self, *args: str) -> str:
        return self._text(*args)


class NoVersionTool(FakeTool):
    version_args: ClassVar[Sequence[str] | None] = None


def make(run: FakeRun, timeout: float = 30.0) -> FakeTool:
    return FakeTool(Path("/work"), run=run, timeout=timeout)


def test_version_args_none_skips_version_check() -> None:
    run = FakeRun(stdout="out\n", version_returncode=1)
    tool = NoVersionTool(Path("/work"), run=run)
    assert tool.text("a") == "out"
    with pytest.raises(ToolError, match="faketool has no version flag"):
        _ = tool.version


def test_runs_executable_then_args() -> None:
    run = FakeRun()
    make(run).text("a", "b")
    assert run.argv == ["faketool", "a", "b"]


def test_passes_cwd() -> None:
    run = FakeRun()
    make(run).text("a")
    assert run.kwargs["cwd"] == Path("/work")


def test_passes_timeout() -> None:
    run = FakeRun()
    make(run, timeout=7.5).text("a")
    assert run.kwargs["timeout"] == 7.5


def test_requests_captured_text_without_check() -> None:
    run = FakeRun()
    make(run).text("a", input="in")
    assert run.kwargs["capture_output"] is True
    assert run.kwargs["text"] is True
    assert run.kwargs["check"] is False
    assert run.kwargs["input"] == "in"


def test_text_returns_stripped_stdout() -> None:
    assert make(FakeRun(stdout="  out\n")).text("a") == "out"


def test_nonzero_exit_raises_tool_error() -> None:
    with pytest.raises(ToolError):
        make(FakeRun(returncode=2)).text("a")


def test_tool_error_holds_argv() -> None:
    with pytest.raises(ToolError) as info:
        make(FakeRun(returncode=2)).text("a", "b")
    assert info.value.argv == ("faketool", "a", "b")


def test_tool_error_holds_returncode() -> None:
    with pytest.raises(ToolError) as info:
        make(FakeRun(returncode=3)).text("a")
    assert info.value.returncode == 3


def test_tool_error_holds_stderr() -> None:
    with pytest.raises(ToolError) as info:
        make(FakeRun(returncode=1, stderr="bad thing")).text("a")
    assert info.value.stderr == "bad thing"


def test_os_error_raises_tool_error() -> None:
    with pytest.raises(ToolError) as info:
        make(FakeRun(raises=FileNotFoundError("nope"))).text("a")
    assert info.value.returncode is None


def test_timeout_raises_tool_error() -> None:
    expired = subprocess.TimeoutExpired(["faketool"], 1.0)
    with pytest.raises(ToolError) as info:
        make(FakeRun(raises=expired)).text("a")
    assert info.value.returncode is None


def test_json_returns_parsed_value() -> None:
    assert make(FakeRun(stdout='{"a": [1, null]}')).json("a") == {"a": [1, None]}


def test_invalid_json_raises_tool_error() -> None:
    with pytest.raises(ToolError):
        make(FakeRun(stdout="not json")).json("a")


def test_default_run_fn_runs_real_process(tmp_path: Path) -> None:
    tool = PythonTool(tmp_path)
    assert tool.text("-c", "print('ok')") == "ok"


def test_env_passed_to_every_call() -> None:
    run = FakeRun()
    env = {"GIT_DIR": "x"}
    tool = FakeTool(Path("/work"), run=run, env=env)
    tool.text("a")
    tool.raw("b")
    assert [call["env"] for call in run.calls] == [env, env]


def test_env_defaults_to_none() -> None:
    run = FakeRun()
    make(run).text("a")
    assert run.kwargs["env"] is None


def test_run_fn_bytes_mode() -> None:
    run = FakeRun(stdout="out")
    result = FakeTool(Path("/work"), run=run).raw("a", input=b"in")
    assert result == b"out"
    assert run.kwargs["text"] is False
    assert run.kwargs["input"] == b"in"


def test_bytes_mode_nonzero_exit_raises_tool_error() -> None:
    with pytest.raises(ToolError) as info:
        FakeTool(Path("/work"), run=FakeRun(returncode=2, stderr="bad")).raw("a")
    assert info.value.returncode == 2
    assert info.value.stderr == "bad"


def test_bytes_mode_os_error_raises_tool_error() -> None:
    with pytest.raises(ToolError):
        FakeTool(Path("/work"), run=FakeRun(raises=FileNotFoundError("nope"))).raw("a")


def test_run_subprocess_forwards_env(tmp_path: Path) -> None:
    result = run_subprocess(
        [sys.executable, "-c", "import os; print(os.environ['ORCH_TEST_ENV'])"],
        cwd=tmp_path,
        input=None,
        timeout=30.0,
        capture_output=True,
        text=True,
        check=False,
        env={"ORCH_TEST_ENV": "forwarded"},
    )
    assert result.stdout.strip() == "forwarded"


def test_run_subprocess_bytes_round_trip(tmp_path: Path) -> None:
    result = run_subprocess(
        [sys.executable, "-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())"],
        cwd=tmp_path,
        input=b"\xff\x00",
        timeout=30.0,
        capture_output=True,
        text=False,
        check=False,
        env=None,
    )
    assert result.stdout == b"\xff\x00"


def test_run_fn_accepts_no_timeout(tmp_path: Path) -> None:
    result = run_subprocess(
        [sys.executable, "-c", "print('ok')"],
        cwd=tmp_path,
        input=None,
        timeout=None,
        capture_output=True,
        text=True,
        check=False,
        env=None,
    )
    assert result.stdout.strip() == "ok"
