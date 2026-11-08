from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACE = (
    ROOT / "orchestra" / "cli.py",
    ROOT / "dashboard" / "frontend" / "e2e" / "serve.py",
    *sorted((ROOT / "dashboard" / "backend").rglob("*.py")),
)


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def test_surface_runs_git_through_git_client() -> None:
    offenders: list[str] = []
    for path in SURFACE:
        for node in ast.walk(_tree(path)):
            if isinstance(node, ast.Name) and node.id == "run_git":
                offenders.append(f"{path.name}: run_git")
            elif isinstance(node, ast.ImportFrom) and any(
                alias.name == "run_git" for alias in node.names
            ):
                offenders.append(f"{path.name}: import run_git")
            elif (
                isinstance(node, (ast.List, ast.Tuple))
                and node.elts
                and isinstance(node.elts[0], ast.Constant)
                and node.elts[0].value == "git"
            ):
                offenders.append(f"{path.name}: git argv")
    assert offenders == []
    uses_git = {
        path.name
        for path in SURFACE
        if any(isinstance(node, ast.Name) and node.id == "Git" for node in ast.walk(_tree(path)))
    }
    assert {"cli.py", "serve.py", "landing.py", "approval.py"} <= uses_git
