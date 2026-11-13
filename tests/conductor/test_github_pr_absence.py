from __future__ import annotations

import ast
from pathlib import Path

import orchestra.conductor as conductor

FORBIDDEN_NAMES = {"GITHUB_TOKEN", "GH_TOKEN"}


def _trees() -> list[tuple[Path, ast.Module]]:
    root = Path(conductor.__file__).parent
    return [
        (path, ast.parse(path.read_text(encoding="utf-8"))) for path in sorted(root.rglob("*.py"))
    ]


def _names_token(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return any(name in node.value for name in FORBIDDEN_NAMES)
    if isinstance(node, ast.Name):
        return node.id in FORBIDDEN_NAMES
    return isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_NAMES


def test_conductor_has_no_token_reference() -> None:
    found: list[str] = []
    for path, tree in _trees():
        for node in ast.walk(tree):
            if _names_token(node):
                found.append(path.name)
    assert found == []


def test_conductor_imports_no_urllib() -> None:
    found: list[str] = []
    for path, tree in _trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            if any(module.split(".")[0] == "urllib" for module in modules):
                found.append(f"{path.name}:{node.lineno}")
    assert found == []
