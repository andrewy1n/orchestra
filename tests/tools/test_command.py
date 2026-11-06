from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, overload

from orchestra.tools import CliTool, Command, CommandResult


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
        if self.raises is not None:
            raise self.raises
        return subprocess.CompletedProcess(list(argv), self.returncode, self.stdout, self.stderr)


def test_command_is_not_a_cli_tool() -> None:
    assert not issubclass(Command, CliTool)
    assert not hasattr(Command, "executable")
    assert not hasattr(Command, "version")


def test_run_returns_command_result(tmp_path: Path) -> None:
    fake = FakeRun(stdout="out", returncode=3)
    result = Command(run=fake).run(["echo", "hi"], cwd=tmp_path, env={"A": "1"}, timeout=5.0)
    assert result == CommandResult(3, "out", "", False, False)
    assert fake.argv == ["echo", "hi"]
    assert fake.kwargs["cwd"] == tmp_path
    assert fake.kwargs["env"] == {"A": "1"}
    assert fake.kwargs["timeout"] == 5.0


def test_shell_runs_through_sh_c(tmp_path: Path) -> None:
    fake = FakeRun()
    Command(run=fake).shell("a | b", cwd=tmp_path)
    assert fake.argv == ["sh", "-c", "a | b"]


def test_command_result_fields() -> None:
    result = CommandResult(0, "o", "e", False, False)
    assert (result.returncode, result.stdout, result.stderr) == (0, "o", "e")
    assert (result.timed_out, result.missing) == (False, False)


def test_output_joins_stdout_and_stderr(tmp_path: Path) -> None:
    result = Command(run=FakeRun(stdout="out", stderr="err")).run(["x"], cwd=tmp_path)
    assert result.output == "outerr"


def test_timeout_sets_timed_out(tmp_path: Path) -> None:
    error = subprocess.TimeoutExpired(["x"], 1.0, output=b"part", stderr="warn")
    result = Command(run=FakeRun(raises=error)).run(["x"], cwd=tmp_path, timeout=1.0)
    assert result == CommandResult(None, "part", "warn", True, False)


def test_missing_executable_sets_missing(tmp_path: Path) -> None:
    result = Command(run=FakeRun(raises=FileNotFoundError("x"))).run(["x"], cwd=tmp_path)
    assert result == CommandResult(None, "", "", False, True, "x")


def test_command_uses_injected_run(tmp_path: Path) -> None:
    fake = FakeRun(stdout="injected")
    result = Command(run=fake).run(["x"], cwd=tmp_path, input="in")
    assert result.stdout == "injected"
    assert fake.kwargs["input"] == "in"
    assert fake.kwargs["capture_output"] is True
    assert fake.kwargs["text"] is True
    assert fake.kwargs["check"] is False


def test_os_error_text_kept_in_error(tmp_path: Path) -> None:
    result = Command(run=FakeRun(raises=PermissionError("denied: /bin/x"))).run(["x"], cwd=tmp_path)
    assert result == CommandResult(None, "", "", False, False, "denied: /bin/x")


def test_missing_is_true_only_for_file_not_found(tmp_path: Path) -> None:
    absent = Command(run=FakeRun(raises=FileNotFoundError("gone"))).run(["x"], cwd=tmp_path)
    other = Command(run=FakeRun(raises=NotADirectoryError("bad cwd"))).run(["x"], cwd=tmp_path)
    ok = Command(run=FakeRun()).run(["x"], cwd=tmp_path)
    assert (absent.missing, absent.error) == (True, "gone")
    assert (other.missing, other.returncode) == (False, None)
    assert (ok.missing, ok.error) == (False, "")
