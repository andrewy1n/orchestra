"""Git repository context checks for the git-filesystem backend."""

from __future__ import annotations

from pathlib import Path

from orchestra.tools.cli_tool import RunFn, run_subprocess
from orchestra.tools.errors import ToolError, ToolNotFoundError
from orchestra.tools.git import Git


class GitContextError(Exception):
    pass


def assert_git_context(start: Path | None = None, *, run: RunFn = run_subprocess) -> Path:
    start = start or Path.cwd()
    try:
        return Git(start, run=run).root()
    except ToolNotFoundError as exc:
        raise GitContextError("git executable not found") from exc
    except ToolError as exc:
        raise GitContextError(exc.stderr.strip() or str(exc)) from exc
