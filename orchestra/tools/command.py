from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from orchestra.tools.cli_tool import RunFn, run_subprocess


def _text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


@dataclass(frozen=True)
class CommandResult:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool
    missing: bool

    @property
    def output(self) -> str:
        return self.stdout + self.stderr


class Command:
    def __init__(self, *, run: RunFn = run_subprocess) -> None:
        self._run: RunFn = run

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
        input: str | None = None,
    ) -> CommandResult:
        try:
            completed = self._run(
                argv,
                cwd=cwd,
                input=input,
                timeout=timeout,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(None, _text(exc.stdout), _text(exc.stderr), True, False)
        except OSError:
            return CommandResult(None, "", "", False, True)
        return CommandResult(
            completed.returncode,
            _text(completed.stdout),
            _text(completed.stderr),
            False,
            False,
        )

    def shell(
        self,
        line: str,
        *,
        cwd: Path,
        env: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        return self.run(["sh", "-c", line], cwd=cwd, env=env, timeout=timeout)
