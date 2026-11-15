from __future__ import annotations

import shutil
from collections.abc import Sequence
from pathlib import Path

import pytest

from orchestra.canon.derive import attach_derived_all
from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.score.analyze import Report, analyze_phase


@pytest.fixture()
def project(store_template: Path, tmp_path: Path) -> Project:
    root = tmp_path / "repo"
    shutil.copytree(store_template, root)
    return open_store(root)


def _seed_phase(project: Project) -> None:
    project.create(
        record_type="score:effort",
        subject="workflow",
        payload={"goal": "Deliver work", "kind": "deliver"},
    )
    project.create(
        record_type="score:phase",
        subject="phase",
        payload={"title": "Phase", "ordinal": 1, "effort": "workflow", "weight": "light"},
        body=(
            "## Problem\n\nPlan work.\n\n## Approach\n\nRun tasks.\n\n"
            "## Exit criteria\n\nComplete work.\n\n## Requirements\n\n"
            "R1: Detect overlapping write scopes.\n"
        ),
    )
    project.create(
        record_type="score:acceptance",
        subject="phase-check",
        payload={
            "method": "check",
            "phase": "phase",
            "effort": "workflow",
            "verify_command": "true",
            "requirement": "R1",
        },
    )


def _item(
    project: Project,
    subject: str,
    *,
    touches: Sequence[JsonValue] | None = None,
    size: str = "M",
    depends_on: Sequence[str] = (),
) -> Record:
    payload: JsonObject = {
        "title": subject,
        "phase": "phase",
        "kind": "deliver",
        "assignee": "",
        "effort": "workflow",
        "requirements": ["R1"],
        "size": size,
        "depends_on": list(depends_on),
    }
    if touches is not None:
        payload["touches"] = list(touches)
    return project.create(
        record_type="score:work-item",
        subject=subject,
        payload=payload,
        body="## Description\n\nImplement the task.\n",
    )


def _report(project: Project) -> Report:
    records = project.records()
    return analyze_phase(attach_derived_all(records, project.derived(records)), "phase")


def test_same_wave_overlap_reports_tasks_declarations_and_witness(project: Project) -> None:
    _seed_phase(project)
    _item(project, "left", touches=["src/*.py"])
    _item(project, "right", touches=["src/main.py"])

    findings = [f for f in _report(project).findings if f.code == "touches-overlap"]

    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity == "warning"
    assert finding.subject == "left, right"
    assert "src/*.py" in finding.message
    assert "src/main.py" in finding.message


def test_disjoint_scopes_do_not_report_overlap(project: Project) -> None:
    _seed_phase(project)
    _item(project, "left", touches=["src/*.py"])
    _item(project, "right", touches=["tests/*.py"])

    assert not [f for f in _report(project).findings if f.code == "touches-overlap"]


def test_ordering_dependency_removes_same_wave_overlap(project: Project) -> None:
    _seed_phase(project)
    _item(project, "first", touches=["src/*.py"])
    _item(project, "second", touches=["src/main.py"], depends_on=["first"])

    assert not [f for f in _report(project).findings if f.code == "touches-overlap"]


def test_directly_chained_small_tasks_report_merge_candidate(project: Project) -> None:
    _seed_phase(project)
    _item(project, "first", touches=["src/*.py"], size="S")
    _item(project, "second", touches=["src/main.py"], size="XS", depends_on=["first"])

    findings = [f for f in _report(project).findings if f.code == "touches-merge-candidate"]

    assert findings
    finding = findings[0]
    assert finding.severity == "warning"
    assert finding.subject == "first, second"
    assert "src/main.py" in finding.message


def test_directly_chained_medium_task_is_not_a_merge_candidate(project: Project) -> None:
    _seed_phase(project)
    _item(project, "first", touches=["src/*.py"], size="M")
    _item(project, "second", touches=["src/main.py"], size="S", depends_on=["first"])

    assert not [f for f in _report(project).findings if f.code == "touches-merge-candidate"]


@pytest.mark.parametrize("touches", [None, []])
def test_missing_or_empty_scope_does_not_create_a_disjointness_finding(
    project: Project, touches: Sequence[JsonValue] | None
) -> None:
    _seed_phase(project)
    _item(project, "unknown", touches=touches)
    _item(project, "scoped", touches=["src/*.py"])

    findings = _report(project).findings

    assert not [f for f in findings if f.code in {"touches-overlap", "touches-invalid"}]


def test_invalid_touch_patterns_are_errors(project: Project) -> None:
    _seed_phase(project)
    _item(project, "invalid", touches=["src//main.py"])

    findings = [f for f in _report(project).findings if f.code == "touches-invalid"]

    assert findings
    finding = findings[0]
    assert finding.severity == "error"
    assert finding.subject == "invalid"
    assert "src//main.py" in finding.message


def test_findings_are_stably_sorted_and_pair_warnings_are_deduplicated(project: Project) -> None:
    _seed_phase(project)
    _item(project, "zeta", touches=["src/*.py", "src/**"])
    _item(project, "alpha", touches=["src/main.py", "src/*.py"])

    findings = [f for f in _report(project).findings if f.code == "touches-overlap"]

    assert len(findings) == 1
    assert findings[0].subject == "alpha, zeta"
