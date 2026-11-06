from __future__ import annotations

from pathlib import Path
from typing import NoReturn

import pytest

from orchestra.tools import Git
from orchestra.tools.errors import ToolError, ToolNotFoundError, ToolVersionError


def test_tool_error_allows_missing_returncode() -> None:
    error = ToolError("not found", ["gh", "--version"], None, "")
    assert error.returncode is None


def test_tool_version_error_is_a_tool_error() -> None:
    assert isinstance(ToolVersionError("old", ["gh"], 0, ""), ToolError)


def test_missing_executable_raises_tool_not_found(tmp_path: Path) -> None:
    def missing(*args: object, **kwargs: object) -> NoReturn:
        raise FileNotFoundError("git")

    with pytest.raises(ToolNotFoundError) as info:
        Git(tmp_path, run=missing).run("status")  # pyright: ignore[reportArgumentType]
    assert isinstance(info.value, ToolError)
