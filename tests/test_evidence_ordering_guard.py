from __future__ import annotations

import ast
from pathlib import Path

from helpers import write_source

REPO = Path(__file__).resolve().parent.parent
ROOTS = ("orchestra/conductor", "orchestra/score", "dashboard/backend")
PICKS = {"max", "min", "sorted"}
COMPARE_EXEMPT: dict[Path, str] = {
    Path(
        "orchestra/conductor/verification/check.py"
    ): "matches same-second runs on purpose and requires them to agree",
    Path(
        "orchestra/conductor/verification/evidence_recovery.py"
    ): "bounds a red run by its acceptance, not a pick",
}


def _is_recorded_at(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value == "recorded_at"


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _picks_by_recorded_at(node: ast.Call) -> bool:
    if _call_name(node) not in PICKS:
        return False
    return any(
        keyword.arg == "key" and any(_is_recorded_at(inner) for inner in ast.walk(keyword.value))
        for keyword in node.keywords
    )


def _compares_recorded_at(node: ast.Compare) -> bool:
    return any(
        isinstance(side, ast.Subscript) and _is_recorded_at(side.slice)
        for side in (node.left, *node.comparators)
    )


def violations(root: Path) -> list[str]:
    found: list[str] = []
    for base in ROOTS:
        for path in sorted((root / base).rglob("*.py")):
            relative = path.relative_to(root)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            lines: set[int] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "orchestra.canon.query":
                    lines.update(node.lineno for alias in node.names if alias.name == "latest")
                if (
                    isinstance(node, ast.Attribute)
                    and node.attr == "latest"
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "query"
                ):
                    lines.add(node.lineno)
                if isinstance(node, ast.Call) and _picks_by_recorded_at(node):
                    lines.add(node.lineno)
                if (
                    isinstance(node, ast.Compare)
                    and relative not in COMPARE_EXEMPT
                    and _compares_recorded_at(node)
                ):
                    lines.add(node.lineno)
            found.extend(f"{relative}:{line}" for line in sorted(lines))
    return found


def test_evidence_ordering_guard_passes_on_tree() -> None:
    assert violations(REPO) == []


def _seed(tmp_path: Path, relative: str, source: str) -> list[str]:
    write_source(tmp_path / relative, source)
    return violations(tmp_path)


def test_evidence_ordering_guard_fails_on_canon_query_latest_import(tmp_path: Path) -> None:
    found = _seed(
        tmp_path,
        "orchestra/conductor/seeded_latest.py",
        "from orchestra.canon.query import latest\n",
    )
    assert found == ["orchestra/conductor/seeded_latest.py:1"]


def test_evidence_ordering_guard_fails_on_canon_query_latest_call(tmp_path: Path) -> None:
    found = _seed(
        tmp_path,
        "orchestra/score/seeded_latest.py",
        "from orchestra.canon import query\n"
        "\n"
        "\n"
        "def pick(records: list[dict[str, str]]) -> object:\n"
        "    return query.latest(records)\n",
    )
    assert found == ["orchestra/score/seeded_latest.py:5"]


def test_evidence_ordering_guard_fails_on_recorded_at_key_pick(tmp_path: Path) -> None:
    found = _seed(
        tmp_path,
        "dashboard/backend/seeded_pick.py",
        "def pick(records: list[dict[str, str]]) -> dict[str, str]:\n"
        "    return max(records, key=lambda r: r['recorded_at'])\n",
    )
    assert found == ["dashboard/backend/seeded_pick.py:2"]


def test_evidence_ordering_guard_fails_on_recorded_at_comparison(tmp_path: Path) -> None:
    found = _seed(
        tmp_path,
        "orchestra/conductor/seeded_compare.py",
        "def later(a: dict[str, str], b: dict[str, str]) -> bool:\n"
        "    return a['recorded_at'] > b['recorded_at']\n",
    )
    assert found == ["orchestra/conductor/seeded_compare.py:2"]


def test_evidence_ordering_guard_allows_record_order_picks(tmp_path: Path) -> None:
    found = _seed(
        tmp_path,
        "orchestra/score/seeded_ok.py",
        "from orchestra.score.lookups import record_order\n"
        "\n"
        "\n"
        "def pick(records: list[dict[str, str]]) -> dict[str, str]:\n"
        "    return max(records, key=record_order)\n",
    )
    assert found == []
