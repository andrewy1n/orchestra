from __future__ import annotations

import ast
from pathlib import Path

import orchestra.tuner as tuner

PRIVATE_HELPERS = {"_git", "_run_git"}


def test_tuner_runs_git_through_git_client() -> None:
    root = Path(tuner.__file__).parent
    found: list[str] = []
    for path in sorted(root.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Name) and node.id == "run_git":
                found.append(f"{path.name}:{node.lineno} run_git")
            elif isinstance(node, ast.alias) and node.name == "run_git":
                found.append(f"{path.name}:{node.lineno} run_git import")
            elif isinstance(node, ast.FunctionDef) and node.name in PRIVATE_HELPERS:
                found.append(f"{path.name}:{node.lineno} def {node.name}")
            elif isinstance(node, ast.Constant) and node.value == "git":
                found.append(f"{path.name}:{node.lineno} 'git' literal")
    assert found == []
