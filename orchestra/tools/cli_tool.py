from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, Protocol, TypeAlias

from orchestra.tools.errors import ToolError

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


class RunFn(Protocol):
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
    ) -> subprocess.CompletedProcess[str]: ...


def run_subprocess(
    argv: Sequence[str],
    *,
    cwd: Path,
    input: str | None,
    timeout: float,
    capture_output: bool,
    text: bool,
    check: bool,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        input=input,
        timeout=timeout,
        capture_output=capture_output,
        text=text,
        check=check,
        errors="replace",
    )


class CliTool:
    executable: ClassVar[str]

    def __init__(
        self,
        cwd: Path,
        *,
        run: RunFn = run_subprocess,
        timeout: float = 30.0,
    ) -> None:
        self._cwd: Path = cwd
        self._run: RunFn = run
        self._timeout: float = timeout

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

    def _text(self, *args: str, input: str | None = None) -> str:
        return self._execute(args, input).stdout.strip()

    def _json(self, *args: str, input: str | None = None) -> JsonValue:
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
