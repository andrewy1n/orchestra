from __future__ import annotations

import ast
from pathlib import Path

from helpers import write_source

REPO = Path(__file__).resolve().parent.parent
ROOTS = ("orchestra", "dashboard")
OWNERS = frozenset(
    {
        Path("orchestra/score/planning/effort.py"),
        Path("orchestra/composer/records.py"),
        Path("orchestra/conductor/phases/progress/effort_status.py"),
        Path("orchestra/conductor/phases/progress/attention.py"),
    }
)
EFFORT_TYPE = "score:effort"
STATUS_WORDS = {"closed", "dormant", "finished"}
PROMOTED = "promoted"


def _py_files(root: Path) -> list[Path]:
    return [p for base in ROOTS for p in sorted((root / base).rglob("*.py"))]


def merged_from_reads(root: Path) -> list[str]:
    found: list[str] = []
    for path in _py_files(root):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        lines = {
            node.lineno
            for node in ast.walk(tree)
            if (isinstance(node, ast.Constant) and node.value == "merged_from")
            or (isinstance(node, ast.Attribute) and node.attr == "merged_from")
            or (isinstance(node, ast.Name) and node.id == "merged_from")
        }
        found.extend(f"{path.relative_to(root)}:{line}" for line in sorted(lines))
    return found


def _constants(node: ast.AST) -> set[object]:
    return {n.value for n in ast.walk(node) if isinstance(n, ast.Constant)}


def _reads_field(node: ast.AST, field: str) -> bool:
    for n in ast.walk(node):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "get"
            and n.args
            and isinstance(n.args[0], ast.Constant)
            and n.args[0].value == field
        ):
            return True
        if (
            isinstance(n, ast.Subscript)
            and isinstance(n.slice, ast.Constant)
            and n.slice.value == field
        ):
            return True
    return False


def _is_attr(node: ast.AST, name: str) -> bool:
    return any(isinstance(n, ast.Attribute) and n.attr == name for n in ast.walk(node))


def derivations(root: Path) -> list[str]:
    found: list[str] = []
    for path in _py_files(root):
        relative = path.relative_to(root)
        if relative in OWNERS:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        lines: set[int] = set()
        statements = {
            id(child): node
            for node in ast.walk(tree)
            if isinstance(node, ast.stmt)
            for child in ast.walk(node)
            if not isinstance(child, ast.stmt)
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            consts = _constants(node)
            statement = statements.get(id(node), node)
            if (
                consts & STATUS_WORDS
                and _reads_field(node, "status")
                and EFFORT_TYPE in _constants(statement)
            ):
                lines.add(node.lineno)
            if EFFORT_TYPE in consts and _reads_field(node, "record_type"):
                lines.add(node.lineno)
            if PROMOTED in consts and _is_attr(node, "status"):
                lines.add(node.lineno)
        found.extend(f"{relative}:{line}" for line in sorted(lines))
    return found


def test_no_production_code_reads_merged_from() -> None:
    assert merged_from_reads(REPO) == []


def test_no_module_outside_the_owners_derives_effort_state() -> None:
    assert derivations(REPO) == []


def test_merged_from_guard_fails_on_seeded_read(tmp_path: Path) -> None:
    write_source(
        tmp_path / "orchestra" / "seeded_merge.py",
        "def merged(payload: dict[str, object]) -> object:\n"
        "    return payload.get('merged_from')\n",
    )
    assert "orchestra/seeded_merge.py:2" in merged_from_reads(tmp_path)


def test_derivation_guard_fails_on_seeded_closed_filter(tmp_path: Path) -> None:
    write_source(
        tmp_path / "dashboard" / "backend" / "seeded_effort.py",
        "def open_efforts(rows: dict[str, list[dict[str, dict[str, str]]]]) -> list[object]:\n"
        "    return [r for r in rows['score:effort'] if r['payload'].get('status') != 'closed']\n",
    )
    assert "dashboard/backend/seeded_effort.py:2" in derivations(tmp_path)


def test_derivation_guard_fails_on_seeded_effort_record_pick(tmp_path: Path) -> None:
    write_source(
        tmp_path / "orchestra" / "seeded_pick.py",
        "def efforts(records: list[dict[str, str]]) -> list[object]:\n"
        "    return [r for r in records if r['record_type'] == 'score:effort']\n",
    )
    assert "orchestra/seeded_pick.py:2" in derivations(tmp_path)


def test_derivation_guard_fails_on_seeded_home_area(tmp_path: Path) -> None:
    write_source(
        tmp_path / "orchestra" / "seeded_home.py",
        "def home(idea: object) -> bool:\n    return idea.status == 'promoted'\n",
    )
    assert "orchestra/seeded_home.py:2" in derivations(tmp_path)


def test_derivation_guard_ignores_owner_modules(tmp_path: Path) -> None:
    for owner in sorted(OWNERS):
        write_source(tmp_path / owner, "def home(idea):\n    return idea.status == 'promoted'\n")
    assert derivations(tmp_path) == []
