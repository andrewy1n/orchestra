from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOTS = ("orchestra", "dashboard")
CORRECTED_OWNER = Path("orchestra/score/lookups.py")
GENERIC_LAYER = Path("orchestra/canon")
SHIMS = {"latest_landing_record", "proof_packet_record", "phase_place_of_record"}


def _sources(root: Path) -> list[Path]:
    return sorted(path for base in ROOTS for path in (root / base).rglob("*.py"))


def _shim_names(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return [node.name] if node.name in SHIMS else []
    if isinstance(node, ast.Name):
        return [node.id] if node.id in SHIMS else []
    if isinstance(node, ast.Attribute):
        return [node.attr] if node.attr in SHIMS else []
    if isinstance(node, ast.alias):
        return [node.name] if node.name in SHIMS else []
    return []


def _reads_corrects(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "get"
        and any(isinstance(arg, ast.Constant) and arg.value == "corrects" for arg in node.args)
    )


def violations(root: Path) -> list[str]:
    found: list[str] = []
    for path in _sources(root):
        relative = path.relative_to(root)
        generic = GENERIC_LAYER in relative.parents
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            lineno = getattr(node, "lineno", 0)
            found.extend(f"{relative}:{lineno}: {name}" for name in _shim_names(node))
            if relative != CORRECTED_OWNER and not generic and _reads_corrects(node):
                found.append(f"{relative}:{lineno}: corrects")
    return found


def test_r20_no_raw_record_landing_shim_exists() -> None:
    shims = [line for line in violations(REPO) if not line.endswith(": corrects")]

    assert shims == []


def test_r20_only_the_lookup_owner_builds_a_corrected_ids_set() -> None:
    builders = [line for line in violations(REPO) if line.endswith(": corrects")]

    assert builders == []


def test_r20_guard_flags_a_seeded_shim_and_a_seeded_corrected_set(tmp_path: Path) -> None:
    seeded = tmp_path / "orchestra" / "seeded.py"
    seeded.parent.mkdir()
    (tmp_path / "dashboard").mkdir()
    seeded.write_text(
        "def latest_landing_record(records, phase):\n"
        "    return {t for r in records for t in r['relationships'].get('corrects') or []}\n",
        encoding="utf-8",
    )

    assert violations(tmp_path) == [
        "orchestra/seeded.py:1: latest_landing_record",
        "orchestra/seeded.py:2: corrects",
    ]
