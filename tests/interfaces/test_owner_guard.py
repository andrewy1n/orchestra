from __future__ import annotations

import ast
import importlib.util
import itertools
from collections.abc import Iterator
from pathlib import Path

import pytest

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.phase_progress import phase_counts

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARDED_ROOTS = ("orchestra", "dashboard")

_CLOCK = itertools.count()


def _python_files(roots: tuple[str, ...] = GUARDED_ROOTS) -> Iterator[Path]:
    for root in roots:
        yield from sorted((REPO_ROOT / root).rglob("*.py"))


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(REPO_ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    package = _module_name(path).split(".")
    if path.name != "__init__.py":
        package = package[:-1]
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - node.level + 1]
                module = ".".join([*base, *([node.module] if node.module else [])])
            else:
                module = node.module or ""
            found.add(module)
            found.update(f"{module}.{alias.name}" for alias in node.names)
    return found


def importers_of(module: str, roots: tuple[str, ...] = GUARDED_ROOTS) -> list[str]:
    return [
        str(path.relative_to(REPO_ROOT))
        for path in _python_files(roots)
        if module in imported_modules(path)
    ]


def test_derive_removed_module_is_gone() -> None:
    assert importlib.util.find_spec("orchestra.derive") is None


def test_derive_removed_has_no_importers() -> None:
    assert importers_of("orchestra.derive") == []


def _work_item(subject: str, phase: str, state: str) -> Record:
    n = next(_CLOCK)
    payload: JsonObject = {"phase": phase}
    return {
        "id": f"<score:work-item:{subject}-{n}>",
        "record_type": "score:work-item",
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:00:{n:02d}Z",
    }


def _progress(
    records: list[Record], phase: str
) -> tuple[dict[str, int], int, int, tuple[str, ...]]:
    progress = phase_counts(records, phase)
    return progress.counts, progress.done, progress.total, progress.in_progress


_PHASE_CASES: dict[
    str, tuple[list[tuple[str, str, str]], tuple[int, int, int, tuple[str, ...]]]
] = {
    "no_items": ([], (0, 0, 0, ())),
    "all_planned": (
        [("a", "p", "planned"), ("b", "p", "planned")],
        (2, 0, 0, ()),
    ),
    "mixed": (
        [
            ("a", "p", "planned"),
            ("b", "p", "in_progress"),
            ("c", "p", "done"),
            ("d", "p", "done"),
        ],
        (1, 1, 2, ("b",)),
    ),
    "all_done": (
        [("a", "p", "done"), ("b", "p", "done")],
        (0, 0, 2, ()),
    ),
    "withdrawn_excluded": (
        [
            ("a", "p", "in_progress"),
            ("b", "p", "withdrawn"),
            ("c", "p", "done"),
        ],
        (0, 1, 1, ("a",)),
    ),
    "other_phase_excluded": (
        [("a", "p", "in_progress"), ("x", "q", "done"), ("y", "q", "planned")],
        (0, 1, 0, ("a",)),
    ),
}


@pytest.mark.parametrize("case", sorted(_PHASE_CASES))
def test_phase_progress_agrees(case: str) -> None:
    items, (planned, in_progress, done, active) = _PHASE_CASES[case]
    records = [_work_item(*item) for item in items]
    counts, got_done, total, got_active = _progress(records, "p")
    assert counts == {"planned": planned, "in_progress": in_progress, "done": done}
    assert got_done == done
    assert total == planned + in_progress + done
    assert got_active == active
