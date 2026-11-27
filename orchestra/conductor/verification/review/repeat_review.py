"""Repeat phase review inputs: prior failed review, affected callers, expansion."""

from __future__ import annotations

import ast
from collections.abc import Iterator, Sequence
from pathlib import Path, PurePosixPath

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import Record

LANDING_PREFIX = "orchestra/conductor/landing/"
SKIPPED_DIRS = frozenset({".git", ".worktrees", ".venv", "venv", "node_modules", "__pycache__"})


def prior_failed_review(project: Project, phase: str) -> Record | None:
    criterion = f"{phase}-review"
    latest: Record | None = None
    for row in project.list("tuner:check-run"):
        payload = record_payload(row)
        if payload.get("criterion_id") != criterion:
            continue
        if payload.get("result") != "fail" or not payload.get("revision"):
            continue
        latest = row
    return latest


def prior_findings(project: Project, phase: str) -> list[Record]:
    rows = project.list("tuner:finding")
    return [row for row in rows if record_payload(row).get("phase") == phase]


def _module_names(path: str) -> list[str]:
    pure = PurePosixPath(path)
    if pure.suffix != ".py":
        return []
    parts = list(pure.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return [".".join(parts)] if parts else []


def _imports(source: str) -> set[str]:
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
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


def _callers_by_module(repo: Path, modules: set[str]) -> dict[str, list[str]]:
    callers: dict[str, list[str]] = {module: [] for module in modules}
    for path in _python_files(repo):
        relative = path.relative_to(repo).as_posix()
        try:
            imported = _imports(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        for module in modules:
            if module in imported and relative not in _module_names_paths(module):
                callers[module].append(relative)
    return callers


def _module_names_paths(module: str) -> set[str]:
    base = module.replace(".", "/")
    return {f"{base}.py", f"{base}/__init__.py"}


def _changed_modules(changed: Sequence[str]) -> set[str]:
    return {name for path in changed for name in _module_names(path)}


def affected_callers(repo: Path, changed: Sequence[str]) -> list[str]:
    callers = _callers_by_module(repo, _changed_modules(changed))
    return sorted({path for paths in callers.values() for path in paths})


def _is_schema_snapshot(path: str) -> bool:
    pure = PurePosixPath(path)
    return pure.suffix == ".json" and "schemas" in pure.parts[:-1]


def needs_expansion(repo: Path, changed: Sequence[str]) -> bool:
    if any(_is_schema_snapshot(path) or path.startswith(LANDING_PREFIX) for path in changed):
        return True
    callers = _callers_by_module(repo, _changed_modules(changed))
    return any(len({path.split("/", 1)[0] for path in paths}) > 1 for paths in callers.values())


def changed_paths(diff: str) -> list[str]:
    paths: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            paths.append(line[len("+++ b/") :])
    return paths
