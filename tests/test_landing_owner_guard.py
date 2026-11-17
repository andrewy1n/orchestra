from __future__ import annotations

import ast
import shutil
from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra import views
from orchestra.canon.project import Project

REPO = Path(__file__).resolve().parent.parent
OWNER = Path("orchestra/conductor/landing.py")
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


def _copy(tmp_path: Path) -> None:
    for base in ROOTS:
        shutil.copytree(REPO / base, tmp_path / base, ignore=shutil.ignore_patterns("__pycache__"))


def _new(tmp_path: Path) -> list[str]:
    baseline = set(violations(REPO))
    return [v for v in violations(tmp_path) if v not in baseline]


def test_r22_guard_passes_on_tree() -> None:
    assert violations(REPO) == []


def test_r22_guard_fails_on_seeded_worktree_path(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "orchestra" / "seeded_worktree.py").write_text(
        "from pathlib import Path\n\n\n"
        "def tree(repo: Path, phase: str) -> Path:\n"
        "    return repo / '.worktrees' / phase\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["orchestra/seeded_worktree.py:5"]


def test_r22_guard_fails_on_seeded_branch_name(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "dashboard" / "backend" / "seeded_branch.py").write_text(
        "def branch(phase: str, task: str) -> str:\n    return f'task/{phase}/{task}'\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["dashboard/backend/seeded_branch.py:2"]


def test_r22_guard_fails_on_seeded_packet_lookup(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "scripts" / "seeded_packet.py").write_text(
        "def pick(records, slug):\n"
        "    return [\n"
        "        r for r in records\n"
        "        if r['record_type'] == 'conductor:proof-packet' and r['phase'] == slug\n"
        "    ]\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["scripts/seeded_packet.py:2"]


def test_r22_guard_allows_listing_packets_without_selecting(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "orchestra" / "seeded_listing.py").write_text(
        "def packets(records):\n"
        "    return [r for r in records if r['record_type'] == 'conductor:proof-packet']\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == []


def test_r22_guard_ignores_owner_module(tmp_path: Path) -> None:
    _copy(tmp_path)
    assert not any(v.startswith(str(OWNER)) for v in violations(tmp_path))


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = make_project(tmp_path / "repo")
    seed_effort(project, "alpha")
    return project


def _landing(project: Project, result: str) -> None:
    phase = project.resolve("score:phase", "p1")
    assert "body" in phase
    project.update(phase["id"], transition="in_progress", body=phase["body"] + "\n## Landing\n")
    create(
        project,
        "conductor:landing",
        "p1",
        {
            "phase": "p1",
            "effort": "alpha",
            "number": 7,
            "url": "https://github.com/o/r/pull/7",
            "head_sha": "abc123",
            "result": result,
        },
    )


def test_r21_landed_phase_names_close_as_the_done_step(project: Project) -> None:
    _landing(project, "success")
    records = views.load_records(project)
    phase = project.resolve("score:phase", "p1")

    step = views._phase_close_step(phase, records)

    assert "`orchestra close --phase p1` moves the phase to done" in step
    assert "Awaiting merge: PR 7" in step


def test_r21_unlanded_phase_does_not_tell_agent_to_mark_done(project: Project) -> None:
    _landing(project, "fail")
    records = views.load_records(project)
    phase = project.resolve("score:phase", "p1")

    step = views._phase_close_step(phase, records)

    assert "Run `orchestra gate p1`." in step
    assert "marking the phase done" not in step
    assert "orchestra close" not in step


def test_r21_phase_without_landing_record_does_not_tell_agent_to_mark_done(
    project: Project,
) -> None:
    records = views.load_records(project)
    phase = project.resolve("score:phase", "p1")

    step = views._phase_close_step(phase, records)

    assert "marking the phase done" not in step


def test_r21_schema_modules_answers_open_question_one() -> None:
    text = (REPO / "design" / "canon" / "schema-modules.md").read_text(encoding="utf-8")
    open_questions = text.split("## Open questions", 1)[1]

    assert "close._apply" in text
    assert "Name the orchestra step that moves a phase to `done`" not in open_questions
