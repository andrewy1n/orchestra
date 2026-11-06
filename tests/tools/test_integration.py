from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from orchestra.tools import CliTool, Version


class GitTool(CliTool):
    executable: ClassVar[str] = "git"
    min_version: ClassVar[Version] = Version(2, 0)


def test_git_subclass_reads_real_git_version(tmp_path: Path) -> None:
    tool = GitTool(tmp_path)

    assert tool.version.major >= 2
