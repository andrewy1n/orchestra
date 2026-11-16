from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIT_CLIENT = ROOT / "orchestra" / "tools" / "git.py"


def _passes_rev_parse_head(call: ast.Call) -> bool:
    literals = {arg.value for arg in call.args if isinstance(arg, ast.Constant)}
    return {"rev-parse", "HEAD"} <= literals


def test_commit_reads_use_git_head() -> None:
    offenders = []
    for base in (ROOT / "orchestra", ROOT / "dashboard" / "backend"):
        for path in sorted(base.rglob("*.py")):
            if path == GIT_CLIENT:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and _passes_rev_parse_head(node):
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert offenders == []
