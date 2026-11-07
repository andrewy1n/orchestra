from __future__ import annotations

import ast
from pathlib import Path

CANON = Path(__file__).resolve().parent.parent / "orchestra" / "canon"


def test_canon_runs_git_through_git_client() -> None:
    offenders: list[str] = []
    for path in sorted(CANON.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        allowed: set[int] = set()
        if path.name == "git_backend.py":
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "run_git":
                    allowed.update(id(child) for child in ast.walk(node))
        for node in ast.walk(tree):
            if id(node) in allowed:
                continue
            if isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
                if name == "run_git":
                    offenders.append(f"{path.name}:{node.lineno} run_git call")
            if isinstance(node, ast.Constant) and node.value == "git":
                offenders.append(f"{path.name}:{node.lineno} git literal")
    assert offenders == []
