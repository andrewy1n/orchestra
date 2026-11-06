import pytest

from orchestra.tools.errors import ToolError, ToolVersionError
from orchestra.tools.version import Version, parse_version


def test_parse_reads_first_version_token() -> None:
    assert parse_version("tool 1.2.3 and 4.5.6") == Version(1, 2, 3)
    assert parse_version("tool 2.10") == Version(2, 10, 0)


def test_parse_ignores_suffix() -> None:
    assert parse_version("git 2.39.2+dfsg1") == Version(2, 39, 2)


def test_parse_raises_without_token() -> None:
    with pytest.raises(ValueError):
        parse_version("no version here")


def test_version_orders_and_formats() -> None:
    assert Version(1, 2) < Version(1, 10)
    assert str(Version(1, 2)) == "1.2.0"


def test_tool_error_stores_fields() -> None:
    error = ToolError("boom", ["git", "x"], 2, "bad")
    assert error.argv == ("git", "x")
    assert error.returncode == 2
    assert error.stderr == "bad"
    assert str(error) == "boom"
    assert isinstance(ToolVersionError("m", [], 1, ""), ToolError)
