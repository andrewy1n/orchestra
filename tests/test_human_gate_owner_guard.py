from __future__ import annotations

import ast
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OWNER = Path("orchestra/score/workflow_blockers.py")
ROOTS = ("orchestra", "dashboard/backend", "scripts")
NEEDS = "needs"
SIGNED_BY = "signed_by"
NEEDS_VALUES = {"human", "none"}
EXEMPT: dict[Path, str] = {
    Path("orchestra/conductor/verification.py"): "decides signed evidence for closing verification",
    Path("dashboard/backend/phase.py"): "derives the card stage; stage derivation stays separate",
}


def _names(node: ast.AST, key: str) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and child.value == key:
            return True
        if isinstance(child, ast.Name) and child.id == key:
            return True
        if isinstance(child, ast.Attribute) and child.attr == key:
            return True
    return False


def _constants(node: ast.AST) -> set[object]:
    return {child.value for child in ast.walk(node) if isinstance(child, ast.Constant)}


def _compares_needs(node: ast.Compare) -> bool:
    operands = [node.left, *node.comparators]
    return any(_names(op, NEEDS) for op in operands) and any(
        _constants(op) & NEEDS_VALUES for op in operands
    )


def _tests_signed(node: ast.AST) -> bool:
    if isinstance(node, ast.Compare):
        operands = [node.left, *node.comparators]
        return any(_names(op, SIGNED_BY) for op in operands) and any(
            isinstance(op, ast.Constant) and op.value == "" for op in operands
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return _names(node.operand, SIGNED_BY)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "bool":
        return any(_names(arg, SIGNED_BY) for arg in node.args)
    if isinstance(node, ast.BoolOp):
        return any(not isinstance(v, ast.Compare) and _names(v, SIGNED_BY) for v in node.values)
    return False


def violations(root: Path) -> list[str]:
    found: list[str] = []
    for base in ROOTS:
        for path in sorted((root / base).rglob("*.py")):
            relative = path.relative_to(root)
            if relative == OWNER or relative in EXEMPT:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            lines: set[int] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Compare) and _compares_needs(node):
                    lines.add(node.lineno)
                if _tests_signed(node):
                    lines.add(getattr(node, "lineno", 0))
            found.extend(f"{relative}:{line}" for line in sorted(lines))
    return found


def _copy(tmp_path: Path) -> None:
    for base in ROOTS:
        shutil.copytree(REPO / base, tmp_path / base, ignore=shutil.ignore_patterns("__pycache__"))


def _new(tmp_path: Path) -> list[str]:
    baseline = set(violations(REPO))
    return [v for v in violations(tmp_path) if v not in baseline]


def test_r16_guard_passes_on_tree() -> None:
    assert violations(REPO) == []


def test_r16_guard_fails_on_seeded_finding_rule(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "orchestra" / "seeded_finding.py").write_text(
        "def blocks(record: dict[str, dict[str, str]]) -> bool:\n"
        "    return record['payload'].get('needs') == 'human'\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["orchestra/seeded_finding.py:2"]


def test_r16_guard_fails_on_seeded_unsigned_rule(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "dashboard" / "backend" / "seeded_unsigned.py").write_text(
        "def unsigned(run: dict[str, dict[str, str]]) -> bool:\n"
        "    return run['payload'].get('signed_by', '') == ''\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["dashboard/backend/seeded_unsigned.py:2"]


def test_r16_guard_fails_on_seeded_unsigned_truthiness(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "scripts" / "seeded_truthy.py").write_text(
        "def unsigned(run: dict[str, dict[str, str]]) -> bool:\n"
        "    return not run['payload'].get('signed_by')\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["scripts/seeded_truthy.py:2"]


def test_r16_guard_ignores_writes_that_set_needs_and_signed_by(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "orchestra" / "seeded_write.py").write_text(
        "def payload(signer: str) -> dict[str, str]:\n"
        "    return {'needs': 'human', 'signed_by': signer}\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == []


def test_r16_guard_ignores_owner_module(tmp_path: Path) -> None:
    _copy(tmp_path)
    assert not any(v.startswith(str(OWNER)) for v in violations(tmp_path))
