from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

import pytest

from orchestra.tools.cli_tool import CliTool
from orchestra.tools.errors import ToolError


class FakeRun:
    def __init__(
        self,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
        raises: BaseException | None = None,
    ) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.raises = raises
        self.argv: list[str] = []
        self.kwargs: dict[str, object] = {}

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | None,
        timeout: float,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        self.argv = list(argv)
        self.kwargs = {
            "cwd": cwd,
            "input": input,
            "timeout": timeout,
            "capture_output": capture_output,
            "text": text,
            "check": check,
        }
        if self.raises is not None:
            raise self.raises
        return subprocess.CompletedProcess(list(argv), self.returncode, self.stdout, self.stderr)


class FakeTool(CliTool):
    executable: ClassVar[str] = "faketool"

    def text(self, *args: str, input: str | None = None) -> str:
        return self._text(*args, input=input)

    def json(self, *args: str) -> object:
        return self._json(*args)


class PythonTool(CliTool):
    executable: ClassVar[str] = sys.executable

    def text(self, *args: str) -> str:
        return self._text(*args)


def make(run: FakeRun, timeout: float = 30.0) -> FakeTool:
    return FakeTool(Path("/work"), run=run, timeout=timeout)


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
