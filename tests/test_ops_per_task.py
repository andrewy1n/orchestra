from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from canon_support import REPO, create, make_project

from orchestra.canon.project import Project

PHASE = "ph"
BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n## Requirements\n\nR1: One.\n"
)


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "ops_per_task", REPO / "scripts" / "ops_per_task.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _world(tmp_path: Path, weight: str = "light") -> Project:
    project = make_project(tmp_path)
    create(project, "score:effort", "ef", {"goal": "g", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "P", "ordinal": 1, "effort": "ef", "weight": weight},
        BODY,
    )
    for slug in ("a", "b"):
        item = create(
            project,
            "score:work-item",
            slug,
            {
                "title": slug,
                "phase": PHASE,
                "kind": "deliver",
                "assignee": "",
                "effort": "ef",
                "requirements": ["R1"],
            },
            "## Description\n\nR1: One.\n\n## Approach\n\nDo.",
        )
        project.update(item["id"], record_type="score:work-item", transition="in_progress")
        project.update(item["id"], record_type="score:work-item", transition="done")
        acceptance = create(
            project,
            "score:acceptance",
            slug,
            {
                "method": "check",
                "phase": PHASE,
                "effort": "ef",
                "verify_command": "true",
                "requirement": "R1",
            },
        )
        create(
            project,
            "tuner:check-run",
            slug,
            {
                "criterion_id": acceptance["id"],
                "revision": "abc",
                "result": "pass",
                "effort": "ef",
                "method": "check",
                "signed_by": "",
            },
            "ok",
        )
        create(
            project,
            "conductor:execution-report",
            slug,
            {"work_item": slug, "result": "pass", "verdict": "pass", "revision": "abc"},
            "evidence: ok",
        )
    return project


def _review(project: Project, result: str = "pass") -> None:
    create(
        project,
        "tuner:check-run",
        f"{PHASE}-review",
        {
            "criterion_id": f"{PHASE}-review",
            "revision": "abc",
            "result": result,
            "effort": "ef",
            "method": "review",
            "signed_by": "",
            "evidence_kind": "review",
        },
        "review",
    )


def test_r04_counts_the_operations_of_each_record_type_and_divides_by_tasks(
    tmp_path: Path,
) -> None:
    project = _world(tmp_path)
    counts, tasks = _script().count_operations(project, PHASE)
    assert tasks == 2
    assert counts["score:work-item"] == 6
    assert counts["score:acceptance"] == 2
    assert counts["tuner:check-run"] == 2
    assert counts["conductor:execution-report"] == 2
    assert counts["score:phase"] == 1


def test_r04_prints_the_per_type_table_and_the_per_task_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _world(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert _script().main([PHASE]) == 0
    out = capsys.readouterr().out
    assert "score:work-item" in out and "tuner:check-run" in out
    assert "per task: 6.5" in out


def test_r04_max_fails_when_the_per_task_total_is_above_the_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _world(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert _script().main([PHASE, "--max", "6.5"]) == 0
    assert _script().main([PHASE, "--max", "6"]) == 1


def test_r04_check_loop_needs_a_light_phase_reports_and_a_passing_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _world(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert _script().main([PHASE, "--check-loop"]) == 1
    assert "no passing review check-run" in capsys.readouterr().err
    _review(project)
    assert _script().main([PHASE, "--check-loop"]) == 0


def test_r04_check_loop_rejects_a_full_phase_with_a_specification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _world(tmp_path, weight="full")
    _review(project)
    spec = {"weight": "full", "phase": PHASE, "effort": "ef", "requirements": ["R1"]}
    create(
        project,
        "score:specification",
        PHASE,
        spec,
        "## Requirements\n\nR1: One.\n\n## Acceptance criteria\n\nx\n\n## Constraints\n\nx\n\n## Non-goals\n\nx\n\n## Invariants\n\nx\n\n## Assumptions\n\nx",
    )
    monkeypatch.chdir(tmp_path)
    assert _script().main([PHASE, "--check-loop"]) == 1
    err = capsys.readouterr().err
    assert "not light" in err and "score:specification" in err
