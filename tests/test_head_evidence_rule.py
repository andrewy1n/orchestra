"""Only orchestra/conductor/head_evidence.py decides a check-run pass from result and revision."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("orchestra", "dashboard/backend")
OWNER = "orchestra/conductor/head_evidence.py"

SEEDED_COPY = """
def passes_at_head(run: dict[str, dict[str, str]], head: str) -> bool:
    payload = run["payload"]
    return payload["result"] == "pass" and payload["revision"] == head
"""


def _strings(node: ast.AST) -> set[str]:
    return {
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    }


def _calls_revision_matches(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name == "revision_matches":
                return True
    return False


def _compares(node: ast.AST, text: str) -> bool:
    return any(
        isinstance(child, ast.Compare) and text in _strings(child) for child in ast.walk(node)
    )


def _decides_pass(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    matches_head = _calls_revision_matches(function) or _compares(function, "revision")
    return False


def decides_pass_from_result_and_revision(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(
        _decides_pass(node)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def head_evidence_offenders(repo_root: Path) -> list[str]:
    found: list[str] = []
    for name in SCAN_DIRS:
        for path in sorted((repo_root / name).rglob("*.py")):
            posix = path.relative_to(repo_root).as_posix()
            if posix != OWNER and decides_pass_from_result_and_revision(path):
                found.append(posix)
    return found


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_guard_passes_on_tree() -> None:
    assert head_evidence_offenders(REPO_ROOT) == []


def test_guard_fails_on_seeded_second_copy(tmp_path: Path) -> None:
    _write(tmp_path, "orchestra/conductor/other.py", SEEDED_COPY)
    _write(tmp_path, OWNER, SEEDED_COPY)
    assert head_evidence_offenders(tmp_path) == ["orchestra/conductor/other.py"]
