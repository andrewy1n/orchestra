from __future__ import annotations

import ast
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OWNER = Path("orchestra/conductor/phase_progress.py")
ROOTS = ("orchestra", "dashboard")
STAGE_NAMES = {"spec", "design", "tasks", "execute", "verify", "land", "close"}
DERIVER_DEFS = {
    "derive_stage",
    "derive_stages",
    "derive_reason",
    "stage_reason",
    "_stage",
    "_stage_reason",
    "_plan_ready",
    "_review_ready",
    "_execution_ready",
    "_verification_ready",
    "_verification_gate",
    "_landing_ready",
    "_phase_close_step",
    "_land_reason",
    "_close_state",
}
DERIVER_CALLS = {
    "open_verify_step",
    "verify_step",
    "verify_facts",
    "execution_readiness",
    "verification_readiness",
    "plan_readiness",
    "review_readiness",
    "integration_state",
    "acceptance_holds",
    "requires_integration_report",
}


def _strings(node: ast.AST) -> set[str]:
    return {
        child.value
        for child in ast.iter_child_nodes(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    }


def _is_stage_list(node: ast.AST) -> bool:
    if not isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return False
    names = _strings(node) & STAGE_NAMES
    return {"land", "close"} <= names and len(names) >= 3


def _called(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def violations(root: Path) -> list[str]:
    found: list[str] = []
    for base in ROOTS:
        for path in sorted((root / base).rglob("*.py")):
            relative = path.relative_to(root)
            if relative == OWNER or "node_modules" in relative.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            lines: set[int] = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name in DERIVER_DEFS:
                        lines.add(node.lineno)
                elif _is_stage_list(node):
                    lines.add(getattr(node, "lineno", 0))
                elif isinstance(node, ast.Call) and _called(node.func) in DERIVER_CALLS:
                    lines.add(node.lineno)
            found.extend(f"{relative}:{line}" for line in sorted(lines))
    return found


def _copy(tmp_path: Path) -> None:
    for base in ROOTS:
        shutil.copytree(
            REPO / base,
            tmp_path / base,
            ignore=shutil.ignore_patterns("__pycache__", "node_modules"),
        )


def _new(tmp_path: Path) -> list[str]:
    baseline = set(violations(REPO))
    return [v for v in violations(tmp_path) if v not in baseline]


def test_r18_guard_passes_on_tree() -> None:
    assert violations(REPO) == []


def test_r18_guard_fails_on_seeded_stage_function(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "orchestra" / "seeded_stage.py").write_text(
        "def derive_stages(weight: str) -> list[str]:\n    return [weight]\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["orchestra/seeded_stage.py:1"]


def test_r18_guard_fails_on_seeded_stage_list(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "dashboard" / "backend" / "seeded_list.py").write_text(
        "FULL = ('spec', 'design', 'tasks', 'execute', 'verify', 'land', 'close')\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["dashboard/backend/seeded_list.py:1"]


def test_r18_guard_fails_on_seeded_stage_from_facts(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "orchestra" / "seeded_facts.py").write_text(
        "from orchestra.conductor.phase_progress import verify_step\n\n\n"
        "def _verify_stage(project, records, phase):\n"
        "    return verify_step(project, records, phase)\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["orchestra/seeded_facts.py:5"]


def test_r18_guard_allows_reading_the_assessed_stage(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "orchestra" / "seeded_reader.py").write_text(
        "from orchestra.conductor.phase_progress import assess\n\n\n"
        "def current(facts):\n"
        "    return assess(facts).current\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == []


def test_r18_guard_ignores_owner_module(tmp_path: Path) -> None:
    _copy(tmp_path)
    assert not any(v.startswith(str(OWNER)) for v in violations(tmp_path))
