from __future__ import annotations

import ast
from pathlib import Path

import orchestra.conductor as conductor

FORBIDDEN_IMPORTS = {"run_git", "git_backend"}
LAND = "land.py"


def _git_uses(path: Path) -> list[str]:
    found: list[str] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and any(
            alias.name in FORBIDDEN_IMPORTS or (node.module or "").endswith("git_backend")
            for alias in node.names
        ):
            found.append(f"{path.name}:{node.lineno} imports run_git")
        elif isinstance(node, ast.Name) and node.id in {"run_git", "_git"}:
            found.append(f"{path.name}:{node.lineno} uses {node.id}")
        elif isinstance(node, ast.FunctionDef) and node.name == "_git":
            found.append(f"{path.name}:{node.lineno} defines _git")
        elif isinstance(node, ast.Constant) and node.value == "git":
            found.append(f"{path.name}:{node.lineno} names the git executable")
    return found


def test_conductor_runs_git_through_git_client() -> None:
    root = Path(conductor.__file__).parent
    found: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if path.name != LAND:
            found.extend(_git_uses(path))
    assert found == []
