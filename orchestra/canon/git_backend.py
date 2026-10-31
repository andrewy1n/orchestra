"""Git repository context checks for the git-filesystem backend."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Literal, overload


class GitContextError(Exception):
    pass


@overload
def run_git(
    cwd: Path | str, *args: str, text: Literal[True], **kwargs: object
) -> subprocess.CompletedProcess[str]: ...


@overload
def run_git(
    cwd: Path | str, *args: str, **kwargs: object
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]: ...


def run_git(
    cwd: Path | str, *args: str, **kwargs: object
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    return subprocess.run(  # pyright: ignore[reportCallIssue, reportUnknownVariableType]  # subprocess overloads cannot express unknown kwargs
        ["git", "-C", str(cwd), *args],
        **kwargs,  # pyright: ignore[reportArgumentType, reportCallIssue, reportUnknownVariableType]  # subprocess overloads cannot model exact kwargs forwarding
    )


def git_root(start: Path | None = None) -> Path:
    start = start or Path.cwd()
    try:
        result = run_git(
            start,
            "rev-parse",
            "--show-toplevel",
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise GitContextError("git executable not found") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise GitContextError(detail or "not inside a git repository")
    return Path(result.stdout.strip())


def assert_git_context(start: Path | None = None) -> Path:
    return git_root(start)
