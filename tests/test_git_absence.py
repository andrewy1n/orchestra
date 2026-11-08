from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("orchestra", "dashboard")
TOOLS_PREFIX = "orchestra/tools/"
PRIVATE_HELPERS = {"_git", "_run_git", "_git_head"}


def _sources() -> Iterator[tuple[str, ast.Module]]:
    for name in SCAN_DIRS:
        for path in sorted((REPO_ROOT / name).rglob("*.py")):
            rel = path.relative_to(REPO_ROOT)
            if "node_modules" in rel.parts:
                continue
            yield rel.as_posix(), ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_run_git_is_gone() -> None:
    found: list[str] = []
    for rel, tree in _sources():
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "run_git":
                found.append(f"{rel}:{node.lineno} defines run_git")
            elif isinstance(node, ast.alias) and node.name.split(".")[-1] == "run_git":
                found.append(f"{rel}:{node.lineno} imports run_git")
    assert found == []


def test_no_private_git_helpers() -> None:
    found = [
        f"{rel}:{node.lineno} defines {node.name}"
        for rel, tree in _sources()
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in PRIVATE_HELPERS
    ]
    assert found == []


def test_no_git_argv_outside_tools() -> None:
    found = [
        f"{rel}:{node.lineno} builds a git argv"
        for rel, tree in _sources()
        if not rel.startswith(TOOLS_PREFIX)
        for node in ast.walk(tree)
        if isinstance(node, ast.List)
        and node.elts
        and isinstance(node.elts[0], ast.Constant)
        and node.elts[0].value == "git"
    ]
    assert found == []
