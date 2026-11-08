from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NoReturn

import pytest

from orchestra.canon.git_backend import GitContextError, git_root


def test_git_root_raises_context_error_when_git_missing(tmp_path: Path) -> None:
    def missing(
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | None,
        timeout: float | None,
        capture_output: bool,
        text: bool,
        check: bool,
        env: Mapping[str, str] | None,
    ) -> NoReturn:
        raise FileNotFoundError("git")

    with pytest.raises(GitContextError, match="git executable not found"):
        git_root(tmp_path, run=missing)  # pyright: ignore[reportArgumentType]
