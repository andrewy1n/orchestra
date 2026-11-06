"""Git repository context checks for the git-filesystem backend."""

from __future__ import annotations

from pathlib import Path

from orchestra.tools.cli_tool import RunFn, run_subprocess
from orchestra.tools.errors import ToolError
from orchestra.tools.git import Git


class GitContextError(Exception):
    pass


def git_root(start: Path | None = None, *, run: RunFn = run_subprocess) -> Path:
    start = start or Path.cwd()
    try:
        result = Git(start, run=run).run("rev-parse", "--show-toplevel")
    except ToolError as exc:
        raise GitContextError("git executable not found") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise GitContextError(detail or "not inside a git repository")
    return Path(result.stdout.strip())


def assert_git_context(start: Path | None = None) -> Path:
    return git_root(start)
