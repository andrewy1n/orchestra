"""Components import only the components below them."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE = REPO_ROOT / "orchestra"
COMPONENTS = ("canon", "score", "composer", "conductor", "tuner", "stage")
ALLOWED = {
    "canon": {"canon"},
    "score": {"canon", "score"},
    "composer": {"canon", "score", "composer"},
    "tuner": {"canon", "tuner"},
    "conductor": {"canon", "score", "tuner", "conductor"},
    "stage": {"canon", "score", "composer", "tuner", "conductor", "stage", "top"},
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
            found.extend((node.lineno, alias.name) for alias in node.names if alias.name.startswith("orchestra."))
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
