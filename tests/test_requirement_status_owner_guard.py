from __future__ import annotations

import ast
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OWNER = Path("orchestra/conductor/requirements.py")
ROOTS = ("orchestra", "dashboard")
STATUS_WORDS = {"verified", "unverified"}
CONSTRUCTOR = "RequirementStatus"
LINKAGE = "acceptance_requirement_ids"
LINKAGE_EXEMPT: dict[Path, str] = {
    Path("orchestra/score/requirements.py"): "defines the acceptance to requirement link",
    Path("orchestra/score/acceptance.py"): "reads the link into the typed acceptance",
    Path("orchestra/score/analyze.py"): "reports requirement coverage, not status",
    Path("dashboard/backend/phase.py"): "lists the acceptances linked to a requirement for display",
}


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


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
                if isinstance(node, ast.Constant) and node.value in STATUS_WORDS:
                    lines.add(node.lineno)
                if isinstance(node, ast.Call):
                    name = _call_name(node)
                    if name == CONSTRUCTOR:
                        lines.add(node.lineno)
                    if name == LINKAGE and relative not in LINKAGE_EXEMPT:
                        lines.add(node.lineno)
            found.extend(f"{relative}:{line}" for line in sorted(lines))
    return found


def _copy(tmp_path: Path) -> None:
    for base in ROOTS:
        shutil.copytree(REPO / base, tmp_path / base, ignore=shutil.ignore_patterns("__pycache__"))


def _new(tmp_path: Path) -> list[str]:
    baseline = set(violations(REPO))
    return [v for v in violations(tmp_path) if v not in baseline]


def test_r18_guard_passes_on_tree() -> None:
    assert violations(REPO) == []


def test_r18_guard_fails_on_seeded_status_literal(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "orchestra" / "seeded_status.py").write_text(
        "def done(status: str) -> bool:\n    return status == 'verified'\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["orchestra/seeded_status.py:2"]


def test_r18_guard_fails_on_seeded_status_literal_in_dashboard(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "dashboard" / "backend" / "seeded_default.py").write_text(
        "def default() -> str:\n    return 'unverified'\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["dashboard/backend/seeded_default.py:2"]


def test_r18_guard_fails_on_seeded_status_constructor(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "orchestra" / "seeded_build.py").write_text(
        "from orchestra.conductor.requirements import RequirementStatus\n"
        "\n"
        "\n"
        "def build(state: str) -> object:\n"
        "    return RequirementStatus('R1', state)\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["orchestra/seeded_build.py:5"]


def test_r18_guard_fails_on_seeded_requirement_acceptance_linkage(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "orchestra" / "conductor" / "seeded_link.py").write_text(
        "from orchestra.score.requirements import acceptance_requirement_ids\n"
        "\n"
        "\n"
        "def linked(acceptance: dict[str, str], requirement: str) -> bool:\n"
        "    return requirement in acceptance_requirement_ids(acceptance)\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == ["orchestra/conductor/seeded_link.py:5"]


def test_r18_guard_ignores_owner_module(tmp_path: Path) -> None:
    _copy(tmp_path)
    assert not any(v.startswith(str(OWNER)) for v in violations(tmp_path))


def test_r18_guard_ignores_unrelated_strings(tmp_path: Path) -> None:
    _copy(tmp_path)
    (tmp_path / "orchestra" / "seeded_text.py").write_text(
        "REASON = 'requirements not verified: R1'\n",
        encoding="utf-8",
    )
    assert _new(tmp_path) == []
