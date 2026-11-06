from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar, Literal, Protocol, TypeAlias, overload

from orchestra.tools.errors import ToolError, ToolVersionError
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


@overload
def run_subprocess(
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
def run_subprocess(
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


def run_subprocess(
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
        timeout: float = 30.0,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self._cwd: Path = cwd
        self._run: RunFn = run
        self._timeout: float = timeout
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
            raise ToolError(f"cannot run {argv[0]}: {error}", argv, None, "") from error
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
            raise ToolError(f"cannot run {argv[0]}: {error}", argv, None, "") from error
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
