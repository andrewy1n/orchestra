from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, overload

from orchestra.tools.cli_tool import CliTool
from orchestra.tools.version import Version


class ScriptedRun:
    def __init__(
        self,
        tool: type[CliTool],
        responses: Mapping[tuple[str, ...], str | bytes],
        version: Version,
    ) -> None:
        self._responses: dict[tuple[str, ...], str | bytes] = dict(responses)
        self._version_argv: tuple[str, ...] = (tool.executable, "--version")
        self._version_output: str = f"{tool.executable} version {version}"
        self.calls: list[tuple[str, ...]] = []
        self.envs: list[Mapping[str, str] | None] = []

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

    def __call__(
        self,
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
        key = tuple(argv)
        self.calls.append(key)
        self.envs.append(env)
        if key == self._version_argv:
            response: str | bytes = self._version_output
        elif key in self._responses:
            response = self._responses[key]
        else:
            raise AssertionError(f"unscripted call: {list(key)}")
        if text:
            out = response.decode() if isinstance(response, bytes) else response
            return subprocess.CompletedProcess(list(key), 0, out, "")
        raw = response.encode() if isinstance(response, str) else response
        return subprocess.CompletedProcess(list(key), 0, raw, b"")


def scripted(
    tool: type[CliTool],
    responses: Mapping[tuple[str, ...], str | bytes],
    *,
    version: Version | None = None,
) -> ScriptedRun:
    return ScriptedRun(tool, responses, version or tool.min_version)
