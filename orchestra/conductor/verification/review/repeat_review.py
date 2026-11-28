"""Repeat phase review inputs: prior failed review, affected callers, expansion."""

from __future__ import annotations

import ast
from collections.abc import Iterator, Sequence
from pathlib import Path, PurePosixPath

from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.score.lookups import record_order
from orchestra.tuner.evidence.record_facts import RecordShapeError, check_run_facts

LANDING_PREFIX = "orchestra/conductor/landing/"
PRODUCT_ROOT = "orchestra"
SKIPPED_DIRS = frozenset({".git", ".worktrees", ".venv", "venv", "node_modules", "__pycache__"})


def prior_failed_review(project: Project, phase: str) -> Record | None:
    criterion = f"{phase}-review"
    failed: list[Record] = []
    for row in project.list("tuner:check-run"):
        if row["subject"] != criterion:
            continue
        try:
            facts = check_run_facts(row)
        except RecordShapeError as error:
            raise RuntimeError(f"malformed review check-run {row['id']}: {error}") from error
        if facts.criterion_id == criterion and facts.result == "fail" and facts.revision:
            failed.append(row)
    return max(failed, key=record_order) if failed else None


def _module_names(path: str) -> list[str]:
    pure = PurePosixPath(path)
    if pure.suffix != ".py":
        return []
    parts = list(pure.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return [".".join(parts)] if parts else []


def _imports(source: str) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module)
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
    return found


def _python_files(repo: Path) -> Iterator[Path]:
    for path in sorted(repo.rglob("*.py")):
        relative = path.relative_to(repo)
        if not SKIPPED_DIRS.intersection(relative.parts):
            yield path


def _scan(repo: Path) -> tuple[dict[str, set[str]], list[str]]:
    imports: dict[str, set[str]] = {}
    unscanned: list[str] = []
    for path in _python_files(repo):
        relative = path.relative_to(repo).as_posix()
        try:
            imports[relative] = _imports(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError, ValueError):
            unscanned.append(relative)
    return imports, unscanned


def unscanned_files(repo: Path) -> list[str]:
    return _scan(repo)[1]


def _module_paths(module: str) -> set[str]:
    base = module.replace(".", "/")
    return {f"{base}.py", f"{base}/__init__.py"}


def _changed_modules(changed: Sequence[str]) -> set[str]:
    return {name for path in changed for name in _module_names(path)}


def _callers_by_module(repo: Path, modules: set[str]) -> dict[str, list[str]]:
    imports, _ = _scan(repo)
    callers: dict[str, list[str]] = {module: [] for module in modules}
    for relative, imported in imports.items():
        for module in modules:
            if module in imported and relative not in _module_paths(module):
                callers[module].append(relative)
    return callers


def affected_callers(repo: Path, changed: Sequence[str]) -> list[str]:
    callers = _callers_by_module(repo, _changed_modules(changed))
    return sorted({path for paths in callers.values() for path in paths})


def _is_schema_snapshot(path: str) -> bool:
    pure = PurePosixPath(path)
    return pure.suffix == ".json" and "schemas" in pure.parts[:-1]


def package_of(path: str) -> str:
    parts = PurePosixPath(path).parts
    head = parts[0] if parts else ""
    if head == PRODUCT_ROOT and len(parts) > 2:
        return "/".join(parts[:2])
    return head


def needs_expansion(repo: Path, changed: Sequence[str]) -> bool:
    if any(_is_schema_snapshot(path) or path.startswith(LANDING_PREFIX) for path in changed):
        return True
    callers = _callers_by_module(repo, _changed_modules(changed))
    return any(
        len({package_of(path) for path in paths if "tests" not in PurePosixPath(path).parts}) > 1
        for paths in callers.values()
    )
