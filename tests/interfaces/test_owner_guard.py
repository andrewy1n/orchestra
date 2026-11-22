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


VIEWS_RENDER = REPO_ROOT / "orchestra" / "views.py"

VIEWS_RENDER_DECIDERS = (
    "_executor_bits",
    "_assignment_bits",
    "_brief_in_scope",
    "_brief_acceptance_in_scope",
    "_orientation",
)

VIEWS_RENDER_MERGED = (
    "_executor_task",
    "_requirement_lines",
    "_body_sections",
    "_string_list",
)

VIEWS_RENDER_ALLOWLIST: dict[str, str] = {}


def _reads_raw_payload(node: ast.AST) -> bool:
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id == "record_payload":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "get":
            return any(
                isinstance(arg, ast.Constant) and arg.value == "payload" for arg in node.args[:1]
            )
    if isinstance(node, ast.Subscript):
        key = node.slice
        return isinstance(key, ast.Constant) and key.value == "payload"
    return False


def raw_payload_readers(path: Path, names: tuple[str, ...]) -> dict[str, list[int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    wanted = set(names)
    found: dict[str, list[int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted:
            lines = sorted(
                inner.lineno
                for inner in ast.walk(node)
                if isinstance(inner, (ast.Call, ast.Subscript)) and _reads_raw_payload(inner)
            )
            found[node.name] = lines
    return found


def test_raw_payload_readers_detects_each_read_form(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        "def via_call(r):\n    return record_payload(r)\n"
        "def via_subscript(r):\n    return r['payload']\n"
        "def via_get(r):\n    return r.get('payload')\n"
        "def clean(r):\n    return r.get('subject')\n",
        encoding="utf-8",
    )
    found = raw_payload_readers(source, ("via_call", "via_subscript", "via_get", "clean"))
    assert {name: bool(lines) for name, lines in found.items()} == {
        "via_call": True,
        "via_subscript": True,
        "via_get": True,
        "clean": False,
    }


def test_views_render_deciders_exist() -> None:
    found = raw_payload_readers(VIEWS_RENDER, VIEWS_RENDER_DECIDERS)
    assert sorted(found) == sorted(VIEWS_RENDER_DECIDERS)


def test_views_render_merged_helpers_are_gone() -> None:
    assert raw_payload_readers(VIEWS_RENDER, VIEWS_RENDER_MERGED) == {}


def test_views_render_deciders_do_not_read_raw_payloads() -> None:
    found = raw_payload_readers(VIEWS_RENDER, VIEWS_RENDER_DECIDERS)
    offenders = {
        name: lines for name, lines in found.items() if lines and name not in VIEWS_RENDER_ALLOWLIST
    }
    assert offenders == {}


def test_views_render_allowlist_only_names_current_raw_readers() -> None:
    found = raw_payload_readers(VIEWS_RENDER, tuple(VIEWS_RENDER_ALLOWLIST))
    stale = sorted(name for name in VIEWS_RENDER_ALLOWLIST if not found.get(name))
    assert stale == []


DASHBOARD_BACKEND = REPO_ROOT / "dashboard" / "backend"

DASHBOARD_TASK_DECIDERS: dict[str, tuple[str, ...]] = {
    "task.py": (
        "check_from",
        "latest_checks",
        "configured_small_wave_budget",
        "_assigned_at",
        "_task_assignments",
        "_last_record_at",
        "belongs",
        "task_rows",
    ),
    "journal.py": (
        "_phase_for_task",
        "_belongs_to_effort",
        "_assignment_task",
        "load_journal",
    ),
    "records.py": ("records_by_effort",),
}

DASHBOARD_TASK_MERGED: dict[str, tuple[str, ...]] = {
    "records.py": ("section", "items_from_value"),
}

DASHBOARD_TASK_ALLOWLIST: dict[tuple[str, str], str] = {}

_DASHBOARD_TASK_DECIDER_IDS = sorted(
    (module, name) for module, names in DASHBOARD_TASK_DECIDERS.items() for name in names
)


@pytest.mark.parametrize(
    ("module", "name"),
    _DASHBOARD_TASK_DECIDER_IDS,
    ids=[f"dashboard_task-{module}-{name}" for module, name in _DASHBOARD_TASK_DECIDER_IDS],
)
def test_dashboard_task_decider_does_not_read_raw_payload(module: str, name: str) -> None:
    found = raw_payload_readers(DASHBOARD_BACKEND / module, (name,))
    assert name in found
    if (module, name) in DASHBOARD_TASK_ALLOWLIST:
        return
    assert found[name] == []


@pytest.mark.parametrize("module", sorted(DASHBOARD_TASK_MERGED))
def test_dashboard_task_merged_helpers_are_gone(module: str) -> None:
    assert raw_payload_readers(DASHBOARD_BACKEND / module, DASHBOARD_TASK_MERGED[module]) == {}


def test_dashboard_task_allowlist_only_names_current_raw_readers() -> None:
    stale = [
        key
        for key in sorted(DASHBOARD_TASK_ALLOWLIST)
        if not raw_payload_readers(DASHBOARD_BACKEND / key[0], (key[1],)).get(key[1])
    ]
    assert stale == []


DASHBOARD_PHASE_ROWS_DECIDERS: dict[str, tuple[str, ...]] = {
    "phase.py": ("phase_rows", "milestone_rows"),
}

DASHBOARD_PHASE_ROWS_MERGED: dict[str, tuple[str, ...]] = {
    "phase.py": (
        "_milestone_state",
        "_awaits_signoff",
        "phase_elapsed",
        "suite_status_label",
        "_suite_runs_by_name",
        "_suite_label_text",
        "_indexed_suite_label",
        "_short_revision",
    ),
}

DASHBOARD_PHASE_ROWS_ALLOWLIST: dict[tuple[str, str], str] = {}

_DASHBOARD_PHASE_ROWS_DECIDER_IDS = sorted(
    (module, name) for module, names in DASHBOARD_PHASE_ROWS_DECIDERS.items() for name in names
)


@pytest.mark.parametrize(
    ("module", "name"),
    _DASHBOARD_PHASE_ROWS_DECIDER_IDS,
    ids=[
        f"dashboard_phase_rows-{module}-{name}"
        for module, name in _DASHBOARD_PHASE_ROWS_DECIDER_IDS
    ],
)
def test_dashboard_phase_rows_decider_exists(module: str, name: str) -> None:
    assert name in raw_payload_readers(DASHBOARD_BACKEND / module, (name,))


@pytest.mark.parametrize(
    ("module", "name"),
    _DASHBOARD_PHASE_ROWS_DECIDER_IDS,
    ids=[
        f"dashboard_phase_rows-{module}-{name}"
        for module, name in _DASHBOARD_PHASE_ROWS_DECIDER_IDS
    ],
)
def test_dashboard_phase_rows_decider_does_not_read_raw_payload(module: str, name: str) -> None:
    found = raw_payload_readers(DASHBOARD_BACKEND / module, (name,))
    assert name in found
    if (module, name) in DASHBOARD_PHASE_ROWS_ALLOWLIST:
        return
    assert found[name] == []


@pytest.mark.parametrize("module", sorted(DASHBOARD_PHASE_ROWS_MERGED))
def test_dashboard_phase_rows_merged_helpers_are_gone(module: str) -> None:
    found = raw_payload_readers(DASHBOARD_BACKEND / module, DASHBOARD_PHASE_ROWS_MERGED[module])
    assert found == {}


def test_dashboard_phase_rows_allowlist_only_names_current_raw_readers() -> None:
    stale = [
        key
        for key in sorted(DASHBOARD_PHASE_ROWS_ALLOWLIST)
        if not raw_payload_readers(DASHBOARD_BACKEND / key[0], (key[1],)).get(key[1])
    ]
    assert stale == []


DASHBOARD_PHASE_EVIDENCE_DECIDERS: dict[str, tuple[str, ...]] = {
    "phase.py": ("phase_evidence", "light_specification", "evidence_records_by_phase"),
}

DASHBOARD_PHASE_EVIDENCE_MERGED: dict[str, tuple[str, ...]] = {
    "phase.py": (
        "_requirement_texts",
        "_requirement_view",
        "_derivation_pool",
        "_release_ready",
        "latest_assessment_map",
        "_tasks_by_requirement",
        "_traced_records",
        "_for_phase",
    ),
}

DASHBOARD_PHASE_EVIDENCE_ALLOWLIST: dict[tuple[str, str], str] = {}

_DASHBOARD_PHASE_EVIDENCE_DECIDER_IDS = sorted(
    (module, name) for module, names in DASHBOARD_PHASE_EVIDENCE_DECIDERS.items() for name in names
)


@pytest.mark.parametrize(
    ("module", "name"),
    _DASHBOARD_PHASE_EVIDENCE_DECIDER_IDS,
    ids=[
        f"dashboard_phase_evidence-{module}-{name}"
        for module, name in _DASHBOARD_PHASE_EVIDENCE_DECIDER_IDS
    ],
)
def test_dashboard_phase_evidence_decider_exists(module: str, name: str) -> None:
    assert name in raw_payload_readers(DASHBOARD_BACKEND / module, (name,))


@pytest.mark.parametrize(
    ("module", "name"),
    _DASHBOARD_PHASE_EVIDENCE_DECIDER_IDS,
    ids=[
        f"dashboard_phase_evidence-{module}-{name}"
        for module, name in _DASHBOARD_PHASE_EVIDENCE_DECIDER_IDS
    ],
)
def test_dashboard_phase_evidence_decider_does_not_read_raw_payload(module: str, name: str) -> None:
    found = raw_payload_readers(DASHBOARD_BACKEND / module, (name,))
    assert name in found
    if (module, name) in DASHBOARD_PHASE_EVIDENCE_ALLOWLIST:
        return
    assert found[name] == []


@pytest.mark.parametrize("module", sorted(DASHBOARD_PHASE_EVIDENCE_MERGED))
def test_dashboard_phase_evidence_merged_helpers_are_gone(module: str) -> None:
    found = raw_payload_readers(DASHBOARD_BACKEND / module, DASHBOARD_PHASE_EVIDENCE_MERGED[module])
    assert found == {}


def test_dashboard_phase_evidence_allowlist_only_names_current_raw_readers() -> None:
    stale = [
        key
        for key in sorted(DASHBOARD_PHASE_EVIDENCE_ALLOWLIST)
        if not raw_payload_readers(DASHBOARD_BACKEND / key[0], (key[1],)).get(key[1])
    ]
    assert stale == []
