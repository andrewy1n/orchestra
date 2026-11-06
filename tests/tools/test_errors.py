from __future__ import annotations

from orchestra.tools.errors import ToolError, ToolVersionError


def test_tool_error_allows_missing_returncode() -> None:
    error = ToolError("not found", ["gh", "--version"], None, "")
    assert error.returncode is None


def test_tool_version_error_is_a_tool_error() -> None:
    assert isinstance(ToolVersionError("old", ["gh"], 0, ""), ToolError)
