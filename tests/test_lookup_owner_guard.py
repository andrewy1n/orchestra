from __future__ import annotations

import ast
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OWNER = Path("orchestra/score/lookups.py")
ROOTS = ("orchestra", "dashboard/backend")
PHASE = "score:phase"
GENERIC_LAYER = Path("orchestra/canon")
RESOLVERS = {"resolve", "resolve_subject"}


def _is_phase_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value == PHASE


def _mentions_phase(node: ast.AST) -> bool:
    return any(_is_phase_literal(child) for child in ast.walk(node))


def _mentions_subject(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and child.value == "subject":
            return True
        if isinstance(child, ast.Name) and child.id in {"_subject", "subject"}:
            return True
        if isinstance(child, ast.Attribute) and child.attr in {"subject", "removesuffix"}:
            return True
    return False


def _resolver_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or not node.args:
        return False
    func = node.func
    name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
    return name in RESOLVERS and _is_phase_literal(node.args[0])


def _index_key(node: ast.AST) -> bool:
    if isinstance(node, ast.Subscript):
        key = node.slice
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr != "get" or not node.args:
            return False
        key = node.args[0]
    else:
        return False
    return isinstance(key, ast.Tuple) and bool(key.elts) and _is_phase_literal(key.elts[0])


def _scopes(tree: ast.Module) -> list[ast.AST]:
    scopes: list[ast.AST] = [
        node
        for node in ast.walk(tree)
        if isinstance(
            node,
            (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp, ast.Lambda),
        )
    ]
    scopes.extend(
        node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    return scopes


_SCOPE_NODES = (
    ast.ListComp,
    ast.SetComp,
    ast.GeneratorExp,
    ast.DictComp,
    ast.Lambda,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
)


def _compares(scope: ast.AST) -> list[ast.Compare]:
    found: list[ast.Compare] = []
    pending = list(ast.iter_child_nodes(scope))
    while pending:
        node = pending.pop()
        if isinstance(node, _SCOPE_NODES):
            continue
        if isinstance(node, ast.Compare):
            found.append(node)
        pending.extend(ast.iter_child_nodes(node))
    return found


def _filters_phase_by_subject(scope: ast.AST) -> bool:
    compares = _compares(scope)
    typed = any(_mentions_phase(c) for c in compares)
    if not typed:
        return False
    return any(
        _mentions_subject(c) and not _mentions_phase(c) and isinstance(c.ops[0], ast.Eq)
        for c in compares
    ) or any(_mentions_phase(c) and _mentions_subject(c) for c in compares)


def violations(root: Path) -> list[str]:
    found: list[str] = []
    for base in ROOTS:
        for path in sorted((root / base).rglob("*.py")):
            relative = path.relative_to(root)
            if relative == OWNER or GENERIC_LAYER in relative.parents:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            lines: set[int] = set()
            for node in ast.walk(tree):
                if _resolver_call(node) or _index_key(node):
                    lines.add(node.lineno)
            for scope in _scopes(tree):
                if _filters_phase_by_subject(scope):
                    lines.add(getattr(scope, "lineno", 0))
            found.extend(f"{relative}:{line}" for line in sorted(lines))
    return found


def _new(tmp_path: Path) -> list[str]:
    baseline = set(violations(REPO))
    return [v for v in violations(tmp_path) if v not in baseline]


def test_r18_guard_passes_on_tree() -> None:
    assert violations(REPO) == []


def test_r18_guard_fails_on_seeded_second_phase_lookup(tmp_path: Path) -> None:
    for base in ROOTS:
        shutil.copytree(REPO / base, tmp_path / base, ignore=shutil.ignore_patterns("__pycache__"))
    seeded = tmp_path / "orchestra" / "seeded_phase_lookup.py"
    seeded.write_text(
        "def phase_of(records, slug):\n"
        "    return [\n"
        "        r for r in records\n"
        "        if r['record_type'] == 'score:phase' and r['subject'] == slug\n"
        "    ]\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["orchestra/seeded_phase_lookup.py:2"]


def test_r18_guard_fails_on_seeded_resolve_call(tmp_path: Path) -> None:
    for base in ROOTS:
        shutil.copytree(REPO / base, tmp_path / base, ignore=shutil.ignore_patterns("__pycache__"))
    seeded = tmp_path / "dashboard" / "backend" / "seeded_resolve.py"
    seeded.write_text(
        "def phase_of(index, slug):\n    return index.resolve_subject('score:phase', slug)\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["dashboard/backend/seeded_resolve.py:2"]


def test_r18_guard_ignores_owner_module(tmp_path: Path) -> None:
    for base in ROOTS:
        shutil.copytree(REPO / base, tmp_path / base, ignore=shutil.ignore_patterns("__pycache__"))
    assert not any(v.startswith(str(OWNER)) for v in violations(tmp_path))
