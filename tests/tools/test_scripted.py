from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest

from orchestra.tools import CliTool, Version
from orchestra.tools.testing import ScriptedRun, scripted


class FakeTool(CliTool):
    executable: ClassVar[str] = "faketool"
    min_version: ClassVar[Version] = Version(2, 1, 0)

    def status(self) -> str:
        return self._text("status")


def call(run: ScriptedRun, *argv: str) -> str:
    return run(
        argv,
        cwd=Path("."),
        input=None,
        timeout=1.0,
        capture_output=True,
        text=True,
        check=False,
        env=None,
    ).stdout


def test_replays_canned_stdout() -> None:
    run = scripted(FakeTool, {("faketool", "status"): "clean\n"})
    result = run(
        ["faketool", "status"],
        cwd=Path("."),
        input=None,
        timeout=1.0,
        capture_output=True,
        text=True,
        check=False,
        env=None,
    )
    assert result.stdout == "clean\n"
    assert result.returncode == 0


def test_records_calls() -> None:
    run = scripted(FakeTool, {("faketool", "a"): "1", ("faketool", "b"): "2"})
    call(run, "faketool", "b")
    call(run, "faketool", "a")
    assert run.calls == [("faketool", "b"), ("faketool", "a")]


def test_answers_version_call_with_min_version() -> None:
    run = scripted(FakeTool, {})
    assert call(run, "faketool", "--version") == "faketool version 2.1.0"
    assert FakeTool(Path("."), run=run).version == Version(2, 1, 0)
    other = scripted(FakeTool, {}, version=Version(3, 0, 0))
    assert FakeTool(Path("."), run=other).version == Version(3, 0, 0)


def test_unscripted_call_raises() -> None:
    run = scripted(FakeTool, {("faketool", "status"): "ok"})
    with pytest.raises(AssertionError, match=r"faketool.*bogus"):
        call(run, "faketool", "bogus")


def test_scripted_run_drives_cli_tool_round_trip() -> None:
    run = scripted(FakeTool, {("faketool", "status"): "clean\n"})
    assert FakeTool(Path("."), run=run).status() == "clean"
    assert run.calls == [("faketool", "--version"), ("faketool", "status")]


def test_scripted_records_env() -> None:
    run = scripted(FakeTool, {("faketool", "status"): "ok"})
    env = {"A": "1"}
    FakeTool(Path("."), run=run, env=env).status()
    assert run.envs == [env, env]


def test_scripted_serves_bytes_for_bytes_calls() -> None:
    run = scripted(FakeTool, {("faketool", "blob"): b"\xff\x00"})
    result = run(
        ["faketool", "blob"],
        cwd=Path("."),
        input=b"in",
        timeout=1.0,
        capture_output=True,
        text=False,
        check=False,
        env=None,
    )
    assert result.stdout == b"\xff\x00"
