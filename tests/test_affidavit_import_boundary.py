"""Orchestra must not import affidavit except inside close functions."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("orchestra", "dashboard")
FORBIDDEN = frozenset({"aa", "aa_resolve", "check", "policy", "verdict"})
CLOSE_LIBRARY_MODULES = frozenset(
    {"affidavit.oracle_red", "affidavit.verdict", "affidavit.binding"}
)


def _imported_modules(path: Path) -> list[tuple[int, str, bool]]:
    """Return (lineno, module, function_local) for affidavit imports."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[int, str, bool]] = []

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self._function_depth = 0

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._function_depth += 1
            self.generic_visit(node)
            self._function_depth -= 1

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Import(self, node: ast.Import) -> None:
            local = self._function_depth > 0
            for alias in node.names:
                found.append((node.lineno, alias.name, local))

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if not node.module:
                return
            local = self._function_depth > 0
            if node.module == "affidavit":
                for alias in node.names:
                    found.append((node.lineno, f"affidavit.{alias.name}", local))
            elif node.module.startswith("affidavit."):
                found.append((node.lineno, node.module, local))

    Visitor().visit(tree)
    return found


def _forbidden(module: str) -> bool:
    parts = module.split(".")
    return len(parts) >= 2 and parts[0] == "affidavit" and parts[1] in FORBIDDEN


def _allowed_close_import(path: Path, module: str, function_local: bool) -> bool:
    """A function-local import inside close is the library call; module-level is not."""
    return (
        function_local
        and path == ROOT / "orchestra" / "close_batch.py"
        and module in CLOSE_LIBRARY_MODULES
    )


def test_orchestra_and_dashboard_do_not_import_affidavit_store_client():
    hits: list[str] = []
    for dirname in SCAN_DIRS:
        for path in sorted((ROOT / dirname).rglob("*.py")):
            for lineno, module, function_local in _imported_modules(path):
                if not _forbidden(module):
                    continue
                if _allowed_close_import(path, module, function_local):
                    continue
                rel = path.relative_to(ROOT)
                hits.append(f"{rel}:{lineno}: {module}")
    assert hits == []


def test_close_batch_affidavit_import_is_function_local():
    """Close may import affidavit inside a function; a module-level import is not allowed."""
    path = ROOT / "orchestra" / "close_batch.py"
    affidavit = [
        item
        for item in _imported_modules(path)
        if item[1] == "affidavit" or item[1].startswith("affidavit.")
    ]
    module_level = [
        f"{lineno}: {module}" for lineno, module, local in affidavit if not local
    ]
    assert module_level == [], "module-level affidavit import: " + "; ".join(module_level)
    local_modules = {module for _, module, local in affidavit if local}
    assert local_modules >= CLOSE_LIBRARY_MODULES


def test_import_scan_rejects_module_level_and_allows_function_local(tmp_path):
    sample = tmp_path / "close_batch.py"
    sample.write_text(
        "import affidavit.verdict\n"
        "def close():\n"
        "    from affidavit.binding import recheck\n"
        "    from affidavit.oracle_red import is_assertion_level_red\n"
        "    from affidavit.verdict import run_verdict\n",
        encoding="utf-8",
    )
    # Parse the sample with the same visitor by pointing it at a temp file.
    # Module-level `import affidavit.verdict` is not a close-function import.
    imports = _imported_modules(sample)
    module_level = [module for _, module, local in imports if not local]
    function_local = [module for _, module, local in imports if local]
    assert "affidavit.verdict" in module_level
    assert set(function_local) >= CLOSE_LIBRARY_MODULES
    assert not any(
        _allowed_close_import(sample, module, False) for module in module_level
    )
