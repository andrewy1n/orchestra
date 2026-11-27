from __future__ import annotations

import os
import subprocess
from pathlib import Path

from orchestra.tools.cli_tool import CliTool
from orchestra.tools.errors import ToolError, ToolNotFoundError, ToolTimeoutError


class Lsof(CliTool):
    executable = "lsof"

    def holders(self, directory: Path) -> list[str]:
        argv = [self.executable, "-F", "pc", "+D", str(directory)]
        try:
            result = self._run(
                argv,
                cwd=self._cwd,
                input=None,
                timeout=self._timeout,
                capture_output=True,
                text=True,
                check=False,
                env=self._env,
            )
        except OSError as error:
            raise ToolNotFoundError(f"cannot run {argv[0]}: {error}", argv, None, "") from error
        except subprocess.TimeoutExpired as error:
            raise ToolTimeoutError(
                f"{argv[0]} timed out after {self._timeout}s", argv, None, ""
            ) from error
        if result.returncode == 1 and result.stdout:
            return _parse(result.stdout)
        if result.returncode == 1 and not result.stderr.strip():
            return []
        if result.returncode != 0:
            raise ToolError(
                f"{argv[0]} exited with code {result.returncode}",
                argv,
                result.returncode,
                result.stderr,
            )
        return _parse(result.stdout)


def _parse(output: str) -> list[str]:
    found: list[str] = []
    pid = ""
    for line in output.splitlines():
        if line.startswith("p"):
            pid = line[1:]
        elif line.startswith("c") and pid and pid != str(os.getpid()):
            entry = f"{line[1:]} (pid {pid})"
            if entry not in found:
                found.append(entry)
    return found
