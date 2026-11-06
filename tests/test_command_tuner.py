from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, overload

import pytest

from orchestra.tuner.audit import _run_probe
from orchestra.tuner.runner import run_tests


class _Recorder:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.calls: list[tuple[list[str], dict[str, object]]] = []
        self._done = (returncode, stdout, stderr)

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
        self.calls.append((list(argv), {"cwd": cwd, "env": env}))
        code, out, err = self._done
        if text:
            return subprocess.CompletedProcess(list(argv), code, out, err)
        return subprocess.CompletedProcess(list(argv), code, out.encode(), err.encode())


def test_audit_runs_argv_through_command(tmp_path: Path) -> None:
    recorder = _Recorder(3, "out", "err")
    probe = {"id": "p", "kind": "cli", "argv": ["tool", "--flag"]}
    result = _run_probe(tmp_path, probe, run=recorder)
    assert result == {"exit_code": 3, "stdout": "out", "stderr": "err"}
    argv, kwargs = recorder.calls[0]
    assert argv == ["tool", "--flag"]
    assert kwargs["cwd"] == tmp_path
    assert _run_probe(tmp_path, {"kind": "cli", "argv": "x"}, run=recorder) == {
        "exit_code": 2,
        "stdout": "",
        "stderr": "invalid argv",
    }


def test_runner_runs_tests_through_command(tmp_path: Path) -> None:
    recorder = _Recorder()
    outcomes = run_tests(
        tmp_path, ["a::b", "c::d"], ["pytest", "{tests}", "--x={report}"], run=recorder
    )
    assert outcomes == {"a::b": "not_run", "c::d": "not_run"}
    argv, kwargs = recorder.calls[0]
    assert argv[:3] == ["pytest", "a::b", "c::d"]
    assert argv[3].startswith("--x=")
    assert kwargs["cwd"] == tmp_path


def test_runner_drops_pythonpath_and_pytest_addopts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTHONPATH", "/somewhere")
    monkeypatch.setenv("PYTEST_ADDOPTS", "-x")
    monkeypatch.setenv("KEEP_ME", "1")
    recorder = _Recorder()
    run_tests(tmp_path, ["t"], ["pytest", "{tests}"], run=recorder)
    env = recorder.calls[0][1]["env"]
    assert isinstance(env, dict)
    assert "PYTHONPATH" not in env
    assert "PYTEST_ADDOPTS" not in env
    assert env["KEEP_ME"] == "1"
