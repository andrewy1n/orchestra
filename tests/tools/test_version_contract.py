from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

import pytest

from orchestra.tools.cli_tool import CliTool
from orchestra.tools.errors import ToolError, ToolVersionError
from orchestra.tools.version import Version


class RecordingRun:
    def __init__(self, version_output: str = "tool version 1.2.3\n") -> None:
        self.version_output = version_output
        self.calls: list[list[str]] = []

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
        self.calls.append(list(argv))
        stdout = self.version_output if list(argv)[1:] == ["--version"] else "ok\n"
        return subprocess.CompletedProcess(list(argv), 0, stdout, "")


class VersionedTool(CliTool):
    executable: ClassVar[str] = "vtool"
    min_version: ClassVar[Version] = Version(1, 0)

    def text(self, *args: str) -> str:
        return self._text(*args)


def make(run: RecordingRun) -> VersionedTool:
    return VersionedTool(Path("."), run=run)


def test_first_command_runs_version() -> None:
    run = RecordingRun()
    make(run).text("status")
    assert run.calls == [["vtool", "--version"], ["vtool", "status"]]


def test_later_commands_skip_version() -> None:
    run = RecordingRun()
    tool = make(run)
    tool.text("a")
    tool.text("b")
    assert run.calls == [["vtool", "--version"], ["vtool", "a"], ["vtool", "b"]]


def test_below_minimum_raises_version_error() -> None:
    tool = make(RecordingRun("vtool 0.9.0"))
    with pytest.raises(ToolVersionError) as info:
        tool.text("status")
    assert isinstance(info.value, ToolError)


def test_version_error_names_executable() -> None:
    with pytest.raises(ToolVersionError, match="vtool"):
        make(RecordingRun("0.9.0")).text("status")


def test_version_error_names_found_and_required() -> None:
    with pytest.raises(ToolVersionError) as info:
        make(RecordingRun("0.9.2")).text("status")
    assert "0.9.2" in str(info.value)
    assert "1.0.0" in str(info.value)


def test_require_names_feature() -> None:
    tool = make(RecordingRun("1.2.3"))
    tool.require(Version(1, 2), "widgets")
    with pytest.raises(ToolVersionError, match="widgets"):
        tool.require(Version(2, 0), "widgets")


def test_version_property_returns_parsed_version() -> None:
    assert make(RecordingRun("tool version 1.2.3\n")).version == Version(1, 2, 3)
