from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

from orchestra.tools.cli_tool import CliTool
from orchestra.tools.errors import ToolError
from orchestra.tools.version import Version


@dataclass(frozen=True)
class GitResult:
    returncode: int
    stdout: str
    stderr: str


class Git(CliTool):
    executable: ClassVar[str] = "git"
    min_version: ClassVar[Version] = Version(2, 17)

    def run(self, *args: str, input: str | None = None) -> GitResult:
        self._check_version()
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
        return GitResult(result.returncode, result.stdout, result.stderr)

    def text(self, *args: str, input: str | None = None) -> str:
        result = self.run(*args, input=input)
        if result.returncode != 0:
            raise ToolError(
                f"{self.executable} exited with code {result.returncode}",
                [self.executable, *args],
                result.returncode,
                result.stderr,
            )
        return result.stdout.strip()

    def show_bytes(self, revision: str, path: str) -> bytes | None:
        self._check_version()
        argv: Sequence[str] = [self.executable, "show", f"{revision}:{path}"]
        try:
            result = self._run(
                argv,
                cwd=self._cwd,
                input=None,
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
            return None
        return result.stdout
