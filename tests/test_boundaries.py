"""Components import only the components below them."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # pyright: ignore[reportMissingImports]  # Pytest installs tomli on Python 3.10.

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "orchestra"
COMPONENTS = ("tools", "canon", "score", "composer", "conductor", "tuner", "views", "stage")
ALLOWED = {
    "tools": {"tools"},
    "canon": {"tools", "canon"},
    "score": {"tools", "canon", "score"},
    "composer": {"tools", "canon", "score", "composer"},
    "tuner": {"tools", "canon", "tuner"},
    "conductor": {"tools", "canon", "score", "tuner", "conductor"},
    "views": {"tools", "canon", "score", "composer", "tuner", "conductor", "views"},
    "stage": {
        "tools",
        "canon",
        "score",
        "composer",
        "tuner",
        "conductor",
        "views",
        "stage",
        "top",
    },
}
TOP_MODULES_STAGE_MAY_NOT_IMPORT = {"orchestra.cli"}


def _component(module: str) -> str:
    parts = module.split(".")
    if len(parts) > 1 and parts[1] in COMPONENTS:
        return parts[1]
    return "top"


def _imports(path: Path) -> list[tuple[int, str]]:
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module == "orchestra":
                found.extend((node.lineno, f"orchestra.{alias.name}") for alias in node.names)
            elif node.module.startswith("orchestra."):
                found.append((node.lineno, node.module))
        elif isinstance(node, ast.Import):
            found.extend(
                (node.lineno, alias.name)
                for alias in node.names
                if alias.name.startswith("orchestra.")
            )
    return found


def boundary_violations(package: Path) -> list[str]:
    violations = []
    for path in sorted(package.rglob("*.py")):
        rel = path.relative_to(package.parent)
        owner = _component(".".join(rel.with_suffix("").parts))
        if owner == "top":
            continue
        for lineno, module in _imports(path):
            target = _component(module)
            if target not in ALLOWED[owner]:
                violations.append(f"{rel}:{lineno}: {owner} imports {module}")
            elif owner == "stage" and module in TOP_MODULES_STAGE_MAY_NOT_IMPORT:
                violations.append(f"{rel}:{lineno}: stage imports {module}")
    return violations


def test_components_import_only_downward():
    assert boundary_violations(PACKAGE) == []


def test_scan_rejects_an_upward_import(tmp_path: Path):
    canon = tmp_path / "orchestra" / "canon"
    canon.mkdir(parents=True)
    (canon / "leak.py").write_text("from orchestra.conductor import suite\n", encoding="utf-8")
    stage = tmp_path / "orchestra" / "stage"
    stage.mkdir()
    (stage / "leak.py").write_text("from orchestra import cli\n", encoding="utf-8")
    assert boundary_violations(tmp_path / "orchestra") == [
        "orchestra/canon/leak.py:1: canon imports orchestra.conductor",
        "orchestra/stage/leak.py:1: stage imports orchestra.cli",
    ]


def test_every_component_may_import_tools(tmp_path: Path):
    for component in COMPONENTS:
        if component == "tools":
            continue
        directory = tmp_path / "orchestra" / component
        directory.mkdir(parents=True)
        (directory / "uses_tools.py").write_text(
            "from orchestra.tools import cli_tool\n", encoding="utf-8"
        )
    assert boundary_violations(tmp_path / "orchestra") == []


def test_stage_may_import_views(tmp_path: Path):
    stage = tmp_path / "orchestra" / "stage"
    stage.mkdir(parents=True)
    (stage / "uses_views.py").write_text("from orchestra.views import render\n", encoding="utf-8")
    assert boundary_violations(tmp_path / "orchestra") == []


def test_views_may_not_import_stage(tmp_path: Path):
    views = tmp_path / "orchestra" / "views"
    views.mkdir(parents=True)
    (views / "leak.py").write_text("from orchestra.stage import hooks\n", encoding="utf-8")
    assert boundary_violations(tmp_path / "orchestra") == [
        "orchestra/views/leak.py:1: views imports orchestra.stage"
    ]


def test_pyproject_packages_include_views():
    with (REPO_ROOT / "pyproject.toml").open("rb") as stream:
        packages = tomllib.load(stream)["tool"]["setuptools"]["packages"]
    assert "orchestra.views" in packages
