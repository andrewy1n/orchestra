from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

from orchestra.tools.cli_tool import CliTool
from orchestra.tools.version import Version


class ScriptedRun:
    def __init__(
        self, tool: type[CliTool], responses: Mapping[tuple[str, ...], str], version: Version
    ) -> None:
        self._responses: dict[tuple[str, ...], str] = dict(responses)
        self._version_argv: tuple[str, ...] = (tool.executable, "--version")
        self._version_output: str = f"{tool.executable} version {version}"
        self.calls: list[tuple[str, ...]] = []

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
    ) -> subprocess.CompletedProcess[str]:
        key = tuple(argv)
        self.calls.append(key)
        if key == self._version_argv:
            stdout = self._version_output
        elif key in self._responses:
            stdout = self._responses[key]
        else:
            raise AssertionError(f"unscripted call: {list(key)}")
        return subprocess.CompletedProcess(list(key), 0, stdout, "")


def scripted(
    tool: type[CliTool],
    responses: Mapping[tuple[str, ...], str],
    *,
    version: Version | None = None,
) -> ScriptedRun:
    return ScriptedRun(tool, responses, version or tool.min_version)
