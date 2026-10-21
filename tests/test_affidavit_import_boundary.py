"""Orchestra must not import the affidavit Python package from close-batch."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("orchestra", "dashboard")
FORBIDDEN = frozenset({"aa", "aa_resolve", "check", "policy", "verdict"})


def _imported_modules(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "affidavit":
                for alias in node.names:
                    found.append((node.lineno, f"affidavit.{alias.name}"))
            elif node.module.startswith("affidavit."):
                found.append((node.lineno, node.module))
    return found


def _forbidden(module: str) -> bool:
    parts = module.split(".")
    return len(parts) >= 2 and parts[0] == "affidavit" and parts[1] in FORBIDDEN


def test_orchestra_and_dashboard_do_not_import_affidavit_store_client():
    hits: list[str] = []
    for dirname in SCAN_DIRS:
        for path in sorted((ROOT / dirname).rglob("*.py")):
            for lineno, module in _imported_modules(path):
                if _forbidden(module):
                    rel = path.relative_to(ROOT)
                    hits.append(f"{rel}:{lineno}: {module}")
    assert hits == []


def test_close_batch_does_not_import_affidavit():
    """R8: orchestra close-batch must not import the affidavit package."""
    path = ROOT / "orchestra" / "close_batch.py"
    modules = [module for _, module in _imported_modules(path)]
    affidavit_hits = [m for m in modules if m == "affidavit" or m.startswith("affidavit.")]
    assert affidavit_hits == []
