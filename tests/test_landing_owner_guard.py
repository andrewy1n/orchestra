from __future__ import annotations

import ast
from pathlib import Path

from helpers import write_source

REPO = Path(__file__).resolve().parent.parent
OWNER = Path("orchestra/conductor/landing/landing.py")
ROOTS = ("orchestra", "dashboard/backend", "scripts")
WORKTREES = ".worktrees"
BRANCH_PREFIXES = ("phase/", "task/")
PACKET = "conductor:proof-packet"
PACKET_NAME = "PROOF_PACKET"
PACKET_KEYS = {"phase", "subject", "effort", "revision", "head"}
PATH_BUILDERS = {"Path", "joinpath"}


def _is_text(node: ast.AST, check: str) -> bool:
    return isinstance(node, ast.Constant) and node.value == check


def _builds_worktree_path(node: ast.AST) -> bool:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return _is_text(node.right, WORKTREES) or _is_text(node.left, WORKTREES)
    if isinstance(node, ast.Call):
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        return name in PATH_BUILDERS and any(_is_text(arg, WORKTREES) for arg in node.args)
    if isinstance(node, ast.JoinedStr):
        return any(
            isinstance(part, ast.Constant)
            and isinstance(part.value, str)
            and WORKTREES in part.value
            for part in node.values
        )
    return False


def _builds_branch_name(node: ast.AST) -> bool:
    if isinstance(node, ast.JoinedStr) and node.values:
        head = node.values[0]
        return (
            isinstance(head, ast.Constant)
            and isinstance(head.value, str)
            and head.value.startswith(BRANCH_PREFIXES)
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = node.left
        return (
            isinstance(left, ast.Constant)
            and isinstance(left.value, str)
            and left.value.startswith(BRANCH_PREFIXES)
        )
    return False


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


def _mentions_packet(node: ast.AST) -> bool:
    return any(
        _is_text(child, PACKET) or (isinstance(child, ast.Name) and child.id == PACKET_NAME)
        for child in ast.walk(node)
    )


def _mentions_key(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and child.value in PACKET_KEYS:
            return True
        if isinstance(child, ast.Name) and child.id in PACKET_KEYS:
            return True
        if isinstance(child, ast.Attribute) and child.attr in PACKET_KEYS:
            return True
    return False


def _selects_packet(scope: ast.AST) -> bool:
    compares = _compares(scope)
    if not any(_mentions_packet(c) for c in compares):
        return False
    return any(_mentions_key(c) and not _mentions_packet(c) for c in compares)


def violations(root: Path) -> list[str]:
    found: list[str] = []
    for base in ROOTS:
        for path in sorted((root / base).rglob("*.py")):
            relative = path.relative_to(root)
            if relative == OWNER:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            lines: set[int] = set()
            for node in ast.walk(tree):
                if _builds_worktree_path(node) or _builds_branch_name(node):
                    lines.add(getattr(node, "lineno", 0))
                if isinstance(node, _SCOPE_NODES) and _selects_packet(node):
                    lines.add(node.lineno)
            found.extend(f"{relative}:{line}" for line in sorted(lines))
    return found


def test_r22_guard_passes_on_tree() -> None:
    assert violations(REPO) == []


def test_r22_guard_fails_on_seeded_worktree_path(tmp_path: Path) -> None:
    write_source(
        tmp_path / "orchestra" / "seeded_worktree.py",
        "from pathlib import Path\n\n\n"
        "def tree(repo: Path, phase: str) -> Path:\n"
        "    return repo / '.worktrees' / phase\n",
    )
    assert violations(tmp_path) == ["orchestra/seeded_worktree.py:5"]


def test_r22_guard_fails_on_seeded_branch_name(tmp_path: Path) -> None:
    write_source(
        tmp_path / "dashboard" / "backend" / "seeded_branch.py",
        "def branch(phase: str, task: str) -> str:\n    return f'task/{phase}/{task}'\n",
    )
    assert violations(tmp_path) == ["dashboard/backend/seeded_branch.py:2"]


def test_r22_guard_fails_on_seeded_packet_lookup(tmp_path: Path) -> None:
    write_source(
        tmp_path / "scripts" / "seeded_packet.py",
        "def pick(records, slug):\n"
        "    return [\n"
        "        r for r in records\n"
        "        if r['record_type'] == 'conductor:proof-packet' and r['phase'] == slug\n"
        "    ]\n",
    )
    assert violations(tmp_path) == ["scripts/seeded_packet.py:2"]


def test_r22_guard_allows_listing_packets_without_selecting(tmp_path: Path) -> None:
    write_source(
        tmp_path / "orchestra" / "seeded_listing.py",
        "def packets(records):\n"
        "    return [r for r in records if r['record_type'] == 'conductor:proof-packet']\n",
    )
    assert violations(tmp_path) == []


def test_r22_guard_ignores_owner_module(tmp_path: Path) -> None:
    write_source(tmp_path / OWNER, "def branch(phase, task):\n    return f'task/{phase}/{task}'\n")
    assert violations(tmp_path) == []
