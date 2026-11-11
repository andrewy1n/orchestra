from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create
from test_ops_per_task import BODY, PHASE, _script, _world

from orchestra.canon import record_payload
from orchestra.metrics import ops


def test_r14_count_operations_counts_each_record_type_and_the_tasks(tmp_path: Path) -> None:
    project = _world(tmp_path)
    counts, tasks = ops.count_operations(project, PHASE)
    assert tasks == 2
    assert counts["score:work-item"] == 6
    assert counts["score:acceptance"] == 2
    assert counts["tuner:check-run"] == 2
    assert counts["conductor:execution-report"] == 2
    assert counts["score:phase"] == 1


def test_r14_count_equals_the_count_of_the_script(tmp_path: Path) -> None:
    project = _world(tmp_path)
    assert ops.count_operations(project, PHASE) == _script().count_operations(project, PHASE)


def test_r14_script_prints_the_package_per_task_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _world(tmp_path)
    counts, tasks = ops.count_operations(project, PHASE)
    monkeypatch.chdir(tmp_path)
    assert _script().main([PHASE]) == 0
    assert f"per task: {sum(counts.values()) / tasks:.1f}" in capsys.readouterr().out


def test_r14_script_delegates_to_the_package() -> None:
    script = _script()
    assert script.count_operations is ops.count_operations
    assert script.tasks_of is ops.tasks_of
    assert script.belongs_to is ops.belongs_to


def test_r14_tasks_of_returns_the_active_successor_once(tmp_path: Path) -> None:
    project = _world(tmp_path)
    record = project.resolve("score:work-item", "a")
    project.supersede(record["id"], record_type="score:work-item", payload={"title": "a2"})
    tasks = ops.tasks_of(project.records(), PHASE)
    assert sorted(t["subject"] for t in tasks) == ["a", "b"]
    assert all(t["lifecycle_state"] != "superseded" for t in tasks)


def test_r14_tasks_of_ignores_other_phases_and_withdrawn_items(tmp_path: Path) -> None:
    project = _world(tmp_path)
    create(
        project,
        "score:phase",
        "elsewhere",
        {"title": "E", "ordinal": 2, "effort": "ef", "weight": "light"},
        BODY,
    )
    create(
        project,
        "score:work-item",
        "other",
        {
            "title": "o",
            "phase": "elsewhere",
            "kind": "deliver",
            "assignee": "",
            "effort": "ef",
            "requirements": ["R1"],
        },
        "## Description\n\nR1: One.\n\n## Approach\n\nDo.",
    )
    gone = create(
        project,
        "score:work-item",
        "gone",
        {
            "title": "g",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": "ef",
            "requirements": ["R1"],
        },
        "## Description\n\nR1: One.\n\n## Approach\n\nDo.",
    )
    project.update(gone["id"], record_type="score:work-item", transition="withdrawn")
    assert {t["subject"] for t in ops.tasks_of(project.records(), PHASE)} == {"a", "b"}
    assert [t["subject"] for t in ops.tasks_of(project.records(), "elsewhere")] == ["other"]


def test_r14_belongs_to_matches_phase_records_and_reports_of_its_tasks(tmp_path: Path) -> None:
    project = _world(tmp_path)
    records = project.records()
    subjects = {"a", "b"}
    phase_record = next(r for r in records if r["record_type"] == "score:phase")
    report = next(r for r in records if r["record_type"] == "conductor:execution-report")
    effort = next(r for r in records if r["record_type"] == "score:effort")
    assert ops.belongs_to(phase_record, PHASE, set(), subjects)
    assert ops.belongs_to(report, PHASE, set(), subjects)
    assert not ops.belongs_to(report, PHASE, set(), {"zzz"})
    assert not ops.belongs_to(effort, PHASE, set(), subjects)


def test_r14_belongs_to_matches_check_runs_by_acceptance_or_subject_prefix(tmp_path: Path) -> None:
    project = _world(tmp_path)
    records = project.records()
    run = next(r for r in records if r["record_type"] == "tuner:check-run")
    acceptance_id = record_payload(run)["criterion_id"]
    assert ops.belongs_to(run, "unrelated", {acceptance_id}, set())
    assert not ops.belongs_to(run, "unrelated", set(), set())


def test_r14_counting_leaves_the_store_unchanged(tmp_path: Path) -> None:
    project = _world(tmp_path)
    before = project.records()
    ops.count_operations(project, PHASE)
    assert project.records() == before


def test_r14_a_phase_without_work_items_has_zero_tasks(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _, tasks = ops.count_operations(project, "no-such-phase")
    assert tasks == 0
