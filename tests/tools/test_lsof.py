from __future__ import annotations

import os
from pathlib import Path

import pytest
from test_cli_tool import FakeRun

from orchestra.tools.errors import ToolError
from orchestra.tools.lsof import Lsof

WORK = Path("/work")


def test_holders_lists_processes_when_lsof_exits_one_with_output() -> None:
    run = FakeRun(stdout="p100\ncclaude\nfcwd\np200\ncnode\n", returncode=1)
    assert Lsof(WORK, run=run).holders(WORK) == ["claude (pid 100)", "node (pid 200)"]


def test_holders_is_empty_when_lsof_exits_one_with_no_output() -> None:
    assert Lsof(WORK, run=FakeRun(returncode=1)).holders(WORK) == []


def test_holders_skips_the_calling_process() -> None:
    run = FakeRun(stdout=f"p{os.getpid()}\ncpytest\n", returncode=1)
    assert Lsof(WORK, run=run).holders(WORK) == []


def test_holders_fails_when_lsof_exits_one_with_only_stderr() -> None:
    run = FakeRun(stderr="lsof: cannot read the table", returncode=1)
    with pytest.raises(ToolError):
        Lsof(WORK, run=run).holders(WORK)


def test_holders_fails_on_an_exit_code_above_one() -> None:
    with pytest.raises(ToolError):
        Lsof(WORK, run=FakeRun(returncode=2)).holders(WORK)


def test_holders_fails_when_lsof_is_missing() -> None:
    with pytest.raises(ToolError):
        Lsof(WORK, run=FakeRun(raises=FileNotFoundError("lsof"))).holders(WORK)


def test_holders_asks_lsof_to_suppress_warnings() -> None:
    run = FakeRun(returncode=1)
    Lsof(WORK, run=run).holders(WORK)
    assert "-w" in run.argv
