from __future__ import annotations

import json
import os
import signal
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import IO, ClassVar, Literal, Protocol, TypeAlias, overload

from orchestra.tools.errors import ToolError, ToolNotFoundError, ToolVersionError
from orchestra.tools.version import Version
from orchestra.tools.version import parse_version as _parse_version

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


class RunFn(Protocol):
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


class ProcessHandle:
    def __init__(self, process: subprocess.Popen[bytes]) -> None:
        self._process: subprocess.Popen[bytes] = process

    @property
    def returncode(self) -> int | None:
        return self._process.poll()

    def wait(self, timeout: float | None = None) -> int:
        try:
            return self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            raise ToolError(
                f"process timed out after {timeout}s", [str(self._process.args)], None, ""
            ) from error

    def terminate_group(self) -> None:
        self._signal_group(signal.SIGTERM)

    def kill_group(self) -> None:
        self._signal_group(signal.SIGKILL)

    def _signal_group(self, signum: int) -> None:
        if os.name != "posix":
            raise ToolError("process-group signals require a Unix host", [], None, "")
        try:
            os.killpg(self._process.pid, signum)
        except ProcessLookupError:
            return
        except OSError as error:
            raise ToolError(f"cannot signal process group: {error}", [], None, "") from error


@overload
def run_subprocess(
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
def run_subprocess(
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


def run_subprocess(
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
    if text:
        assert input is None or isinstance(input, str)
        return subprocess.run(
            list(argv),
            cwd=cwd,
            input=input,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            check=check,
            env=env,
            errors="replace",
        )
    assert input is None or isinstance(input, bytes)
    return subprocess.run(
        list(argv),
        cwd=cwd,
        input=input,
        timeout=timeout,
        capture_output=capture_output,
        text=False,
        check=check,
        env=env,
    )


class CliTool:
    executable: ClassVar[str]
    min_version: ClassVar[Version] = Version(0, 0)

    def __init__(
        self,
        cwd: Path,
        *,
        run: RunFn = run_subprocess,
        timeout: float | None = 30.0,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self._cwd: Path = cwd
        self._run: RunFn = run
        self._timeout: float | None = timeout
        self._env: Mapping[str, str] | None = env
        self._version: Version | None = None

    @classmethod
    def parse_version(cls, output: str) -> Version:
        return _parse_version(output)

    @property
    def version(self) -> Version:
        if self._version is None:
            result = self._execute(["--version"], None)
            try:
                found = self.parse_version(result.stdout)
            except ValueError as error:
                raise ToolError(
                    f"cannot parse {self.executable} version: {error}",
                    [self.executable, "--version"],
                    result.returncode,
                    result.stderr,
                ) from error
            if found < self.min_version:
                raise ToolVersionError(
                    f"{self.executable} version {found} is below required {self.min_version}",
                    [self.executable, "--version"],
                    result.returncode,
                    result.stderr,
                )
            self._version = found
        return self._version

    def _check_version(self) -> None:
        _ = self.version

    def require(self, version: Version, feature: str) -> None:
        found = self.version
        if found < version:
            raise ToolVersionError(
                f"{feature} needs {self.executable} {version} or newer, found {found}",
                [self.executable],
                None,
                "",
            )

    def _execute(self, args: Sequence[str], input: str | None) -> subprocess.CompletedProcess[str]:
        argv = [self.executable, *args]
        try:
            result = self._run(
                argv,
                cwd=self._cwd,
                input=input,
                timeout=self._timeout,
                capture_output=True,
                text=True,
                check=False,
                env=self._env,
            )
        except OSError as error:
            raise ToolNotFoundError(f"cannot run {argv[0]}: {error}", argv, None, "") from error
        except subprocess.TimeoutExpired as error:
            raise ToolError(
                f"{argv[0]} timed out after {self._timeout}s", argv, None, ""
            ) from error
        if result.returncode != 0:
            raise ToolError(
                f"{argv[0]} exited with code {result.returncode}",
                argv,
                result.returncode,
                result.stderr,
            )
        return result

    def _execute_bytes(
        self, args: Sequence[str], input: bytes | None
    ) -> subprocess.CompletedProcess[bytes]:
        argv = [self.executable, *args]
        try:
            result = self._run(
                argv,
                cwd=self._cwd,
                input=input,
                timeout=self._timeout,
                capture_output=True,
                text=False,
                check=False,
                env=self._env,
            )
        except OSError as error:
            raise ToolNotFoundError(f"cannot run {argv[0]}: {error}", argv, None, "") from error
        except subprocess.TimeoutExpired as error:
            raise ToolError(
                f"{argv[0]} timed out after {self._timeout}s", argv, None, ""
            ) from error
        if result.returncode != 0:
            raise ToolError(
                f"{argv[0]} exited with code {result.returncode}",
                argv,
                result.returncode,
                result.stderr.decode("utf-8", errors="replace"),
            )
        return result

    def start_process(
        self,
        argv: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: int | IO[bytes] | None = subprocess.DEVNULL,
        stdout: int | IO[bytes] | None = subprocess.DEVNULL,
        stderr: int | IO[bytes] | None = subprocess.STDOUT,
        pass_fds: Sequence[int] = (),
    ) -> ProcessHandle:
        command = list(argv)
        if os.name != "posix":
            raise ToolError("detached process launch requires a Unix host", command, None, "")
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd or self._cwd,
                env=env if env is not None else self._env,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                close_fds=True,
                pass_fds=tuple(pass_fds),
                start_new_session=True,
            )
        except OSError as error:
            raise ToolNotFoundError(
                f"cannot start {command[0]}: {error}", command, None, ""
            ) from error
        return ProcessHandle(process)

    def _text(self, *args: str, input: str | None = None) -> str:
        self._check_version()
        return self._execute(args, input).stdout.strip()

    def _json(self, *args: str, input: str | None = None) -> JsonValue:
        self._check_version()
        result = self._execute(args, input)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise ToolError(
                f"{self.executable} produced invalid JSON: {error}",
                [self.executable, *args],
                result.returncode,
                result.stderr,
            ) from error
