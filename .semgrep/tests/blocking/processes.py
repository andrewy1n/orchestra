# ruff: noqa: ERA001

import asyncio
import os
from os import execv
from pathlib import Path

from orchestra.tools import CliTool


async def direct_process(command: str) -> None:
    # ruleid: orchestra.process-boundary
    await asyncio.create_subprocess_exec(command)
    # ruleid: orchestra.process-boundary
    await asyncio.create_subprocess_shell(command)
    # ruleid: orchestra.process-boundary
    os.system(command)
    # ruleid: orchestra.process-boundary
    os.execv(command, [command])
    # ruleid: orchestra.process-boundary
    execv(command, [command])
    # ruleid: orchestra.process-boundary
    os.posix_spawn(command, [command], {})


def approved_tool(root: Path, command: str) -> None:
    # ok: orchestra.process-boundary
    CliTool(root).start_process([command])
    # ok: orchestra.process-boundary
    os.path.exists(command)
