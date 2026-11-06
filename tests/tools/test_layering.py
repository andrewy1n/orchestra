from __future__ import annotations

import sys
from pathlib import Path

from test_boundaries import PACKAGE, REPO_ROOT, boundary_violations

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # pyright: ignore[reportMissingImports]


def test_tools_imports_no_component(tmp_path: Path) -> None:
    real = [v for v in boundary_violations(PACKAGE) if v.startswith("orchestra/tools/")]
    assert real == []

    tools = tmp_path / "orchestra" / "tools"
    tools.mkdir(parents=True)
    (tools / "leak.py").write_text("from orchestra.canon import store\n", encoding="utf-8")
    assert boundary_violations(tmp_path / "orchestra") == [
        "orchestra/tools/leak.py:1: tools imports orchestra.canon",
    ]


def test_pyproject_lists_tools_package() -> None:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    packages: list[str] = data["tool"]["setuptools"]["packages"]
    assert "orchestra.tools" in packages
