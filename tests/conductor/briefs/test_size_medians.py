from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import make_project

from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.cli import main
from orchestra.conductor.phases.workflow.workflow_review import record_step_review

EFFORT = "sizing-effort"
PHASE = "sizing"
PHASE_BODY = (
    "## Problem\nSize work.\n"
    "## Approach\nMeasure it.\n"
    "## Exit criteria\nVerify the result.\n"
    "## Landing\nUse a phase worktree.\n"
)
SPEC_BODY = (
    "## Requirements\nR1: Show medians.\n"
    "## Acceptance criteria\nR1 passes.\n"
    "## Constraints\nKeep scope fixed.\n"
    "## Non-goals\nNo unrelated changes.\n"
    "## Invariants\nApproval remains explicit.\n"
    "## Assumptions\nThe store is available.\n"
)
DESIGN_BODY = (
    "## Architecture\nUse workflow records.\n"
    "## Interfaces\nUse typed APIs.\n"
    "## Decisions\nPersist reviews.\n"
    "## Invariants\nDo not infer approval.\n"
    "## Assumptions\nThe phase exists.\n"
    "## Tradeoffs\nKeep writes atomic.\n"
    "## Risks\nStale inputs need review.\n"
)


def _approve_spec(project: Project, artifact: Record) -> None:
    record_step_review(
        project,
        phase=PHASE,
        step="spec",
        artifact=artifact,
        authority="user-approval",
        basis="Approved.",
        source_reviews=[],
    )


def _approve_design(project: Project, artifact: Record) -> None:
    record_step_review(
        project,
        phase=PHASE,
        step="design",
        artifact=artifact,
        authority="user-approval",
        basis="Approved.",
        source_reviews=[],
    )


def _seed(root: Path) -> Project:
    project = make_project(root)
    project.create(
        record_type="score:effort",
        subject=EFFORT,
        payload={"goal": "Sizing", "kind": "deliver"},
    )
    project.create(
        record_type="score:phase",
        subject=PHASE,
        payload={"title": PHASE, "ordinal": 1, "effort": EFFORT},
        body=PHASE_BODY,
    )
    specification = project.create(
        record_type="score:specification",
        subject="sizing-spec",
        payload={"weight": "full", "phase": PHASE, "effort": EFFORT, "requirements": ["R1"]},
        body=SPEC_BODY,
    )
    _approve_spec(project, specification)
    design = project.create(
        record_type="score:design",
        subject="sizing-design",
        payload={"phase": PHASE, "effort": EFFORT, "decisions": []},
        body=DESIGN_BODY,
    )
    _approve_design(project, design)
    return project


def _item(project: Project, slug: str, size: str) -> None:
    project.create(
        record_type="score:work-item",
        subject=slug,
        payload={
            "title": slug,
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "agent",
            "effort": EFFORT,
            "size": size,
        },
        body="## Description\n\nd",
    )


def _report(project: Project, slug: str, duration_s: float) -> None:
    project.create(
        record_type="conductor:execution-report",
        subject=f"{slug}-report-{duration_s}",
        payload={
            "work_item": slug,
            "result": "done",
            "verdict": "pass",
            "revision": "abc123",
            "duration_s": duration_s,
        },
        body="Report.",
    )


def _tasks_brief(root: Path, capsys: pytest.CaptureFixture[str]) -> str:
    code = main(["workflow", "brief", PHASE, "tasks", "--store", str(root)])
    captured = capsys.readouterr()
    assert code == 0, captured.out + captured.err
    return captured.out


def _line(brief: str, size: str) -> str:
    for line in brief.splitlines():
        if line.strip().startswith(f"- {size}: "):
            return line.strip()
    raise AssertionError(f"no measured line for {size}")


def test_medians_print_minutes_and_sample_count_per_size(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _seed(tmp_path)
    _item(project, "small-a", "S")
    _item(project, "small-b", "S")
    _item(project, "small-c", "S")
    _item(project, "large-a", "L")
    _report(project, "small-a", 120)
    _report(project, "small-b", 240)
    _report(project, "small-c", 600)
    _report(project, "large-a", 900)

    brief = _tasks_brief(tmp_path, capsys)

    assert _line(brief, "S") == "- S: 4.0 min median, 3 samples"
    assert _line(brief, "L") == "- L: 15.0 min median, 1 sample"


def test_medians_ignore_reports_without_numeric_duration(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _seed(tmp_path)
    _item(project, "mid-a", "M")
    _report(project, "mid-a", 360)
    project.create(
        record_type="conductor:execution-report",
        subject="mid-a-no-duration",
        payload={
            "work_item": "mid-a",
            "result": "done",
            "verdict": "pass",
            "revision": "abc123",
        },
        body="Report.",
    )

    brief = _tasks_brief(tmp_path, capsys)

    assert _line(brief, "M") == "- M: 6.0 min median, 1 sample"


def test_no_data_for_sizes_without_a_measured_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _seed(tmp_path)
    _item(project, "small-a", "S")
    _item(project, "xl-a", "XL")
    _report(project, "small-a", 180)

    brief = _tasks_brief(tmp_path, capsys)

    assert _line(brief, "XS") == "- XS: no data"
    assert _line(brief, "XL") == "- XL: no data"
    assert _line(brief, "S") == "- S: 3.0 min median, 1 sample"


def test_a_retried_task_counts_once_by_its_latest_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _seed(tmp_path)
    _item(project, "retried", "S")
    _report(project, "retried", 120)
    _report(project, "retried", 600)

    brief = _tasks_brief(tmp_path, capsys)

    assert _line(brief, "S") == "- S: 10.0 min median, 1 sample"


def test_reports_for_unsized_work_do_not_use_up_the_report_limit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = _seed(tmp_path)
    _item(project, "sized", "S")
    _report(project, "sized", 180)
    for index in range(101):
        project.create(
            record_type="score:work-item",
            subject=f"unsized-{index}",
            payload={
                "title": "unsized",
                "phase": PHASE,
                "kind": "deliver",
                "assignee": "agent",
                "effort": EFFORT,
            },
            body="## Description\n\nd",
        )
        _report(project, f"unsized-{index}", 60 + index)

    brief = _tasks_brief(tmp_path, capsys)

    assert _line(brief, "S") == "- S: 3.0 min median, 1 sample"


def test_measured_lines_are_indented_inside_their_bullet(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _seed(tmp_path)

    brief = _tasks_brief(tmp_path, capsys)

    assert "\n  - XS: no data\n" in brief
