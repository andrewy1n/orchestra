from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.project import Project
from orchestra.metrics.phases import PhaseRow, build_phase_rows

SPEC_BODY = (
    "## Requirements\n\nR1: One.\n\n## Acceptance criteria\n\nx\n\n## Constraints\n\nx\n\n"
    "## Non-goals\n\nx\n\n## Invariants\n\nx\n\n## Assumptions\n\nx"
)


class Clock:
    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.value = "2026-11-01T00:00:00+00:00"
        monkeypatch.setattr("orchestra.canon.record.now", lambda: self.value)

    def at(self, value: str) -> None:
        self.value = value


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    return Clock(monkeypatch)


def _phase(
    project: Project,
    name: str,
    effort: str,
    *,
    weight: str | None = "light",
    tasks: int = 0,
    done: bool = True,
) -> None:
    payload: dict = {"title": name, "ordinal": 1, "effort": effort}
    if weight is not None:
        payload["weight"] = weight
    record = create(project, "score:phase", name, payload)
    for index in range(tasks):
        create(
            project,
            "score:work-item",
            f"{name}-t{index}",
            {
                "title": "t",
                "phase": name,
                "kind": "deliver",
                "assignee": "",
                "effort": effort,
                "requirements": ["R1"],
            },
            "## Description\n\nR1: One.\n\n## Approach\n\nDo.",
        )
    if done:
        project.update(record["id"], record_type="score:phase", transition="in_progress")
        project.update(record["id"], record_type="score:phase", transition="done")


def _specification(project: Project, phase: str, effort: str) -> None:
    create(
        project,
        "score:specification",
        phase,
        {"weight": "full", "phase": phase, "effort": effort, "requirements": ["R1"]},
        SPEC_BODY,
    )


def _landing(project: Project, phase: str) -> None:
    create(
        project,
        "conductor:landing",
        phase,
        {"phase": phase, "number": 1, "url": "u", "head_sha": "abc", "result": "success"},
    )


def _proof(project: Project, phase: str, effort: str) -> None:
    create(
        project,
        "conductor:proof-packet",
        phase,
        {"phase": phase, "effort": effort, "revision": "abc", "base": "def", "kind": "mixed"},
    )


def _check_run(project: Project, phase: str, effort: str) -> None:
    create(
        project,
        "tuner:check-run",
        f"{phase}-check",
        {
            "criterion_id": f"{phase}-check",
            "revision": "abc",
            "result": "pass",
            "effort": effort,
            "method": "check",
            "signed_by": "",
        },
        "ok",
    )


def _row(rows: list[PhaseRow], phase: str) -> PhaseRow:
    return next(r for r in rows if r.phase == phase)


def _world(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    create(project, "score:effort", "ef", {"goal": "g", "kind": "deliver"})
    create(project, "score:effort", "other", {"goal": "g", "kind": "deliver"})
    return project


def test_effort_weight_tasks_are_given_for_each_done_phase(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef", weight="light", tasks=2)
    _phase(project, "ph-b", "other", weight="full", tasks=3)
    rows = build_phase_rows(tmp_path)
    a, b = _row(rows, "ph-a"), _row(rows, "ph-b")
    assert (a.effort, a.weight, a.tasks) == ("ef", "light", 2)
    assert (b.effort, b.weight, b.tasks) == ("other", "full", 3)


def test_effort_weight_tasks_skip_phases_that_are_not_done(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef", tasks=1)
    _phase(project, "ph-open", "ef", tasks=1, done=False)
    assert [r.phase for r in build_phase_rows(tmp_path)] == ["ph-a"]


def test_effort_weight_tasks_filter_by_effort(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef", tasks=1)
    _phase(project, "ph-b", "other", tasks=1)
    assert [r.phase for r in build_phase_rows(tmp_path, effort="other")] == ["ph-b"]


def test_landing_time_comes_from_the_landing_record_first(tmp_path: Path, clock: Clock) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    clock.at("2026-11-02T00:00:00+00:00")
    _check_run(project, "ph-a", "ef")
    clock.at("2026-11-03T00:00:00+00:00")
    _proof(project, "ph-a", "ef")
    clock.at("2026-11-04T00:00:00+00:00")
    _landing(project, "ph-a")
    row = _row(build_phase_rows(tmp_path), "ph-a")
    assert row.landing_source == "conductor:landing"
    assert row.landing_time == "2026-11-04T00:00:00+00:00"


def test_landing_time_falls_back_to_the_proof_packet(tmp_path: Path, clock: Clock) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    clock.at("2026-11-02T00:00:00+00:00")
    _check_run(project, "ph-a", "ef")
    clock.at("2026-11-03T00:00:00+00:00")
    _proof(project, "ph-a", "ef")
    row = _row(build_phase_rows(tmp_path), "ph-a")
    assert row.landing_source == "conductor:proof-packet"
    assert row.landing_time == "2026-11-03T00:00:00+00:00"


def test_landing_time_falls_back_to_the_last_check_run(tmp_path: Path, clock: Clock) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    clock.at("2026-11-02T00:00:00+00:00")
    _check_run(project, "ph-a", "ef")
    clock.at("2026-11-05T00:00:00+00:00")
    create(
        project,
        "tuner:check-run",
        "ph-a-later",
        {
            "criterion_id": "ph-a-later",
            "revision": "abc",
            "result": "pass",
            "effort": "ef",
            "method": "check",
            "signed_by": "",
        },
        "ok",
    )
    row = _row(build_phase_rows(tmp_path), "ph-a")
    assert row.landing_source == "tuner:check-run"
    assert row.landing_time == "2026-11-05T00:00:00+00:00"


def test_elapsed_runs_from_the_first_specification_to_landing(tmp_path: Path, clock: Clock) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef", weight="full")
    clock.at("2026-11-02T00:00:00+00:00")
    _specification(project, "ph-a", "ef")
    clock.at("2026-11-02T06:00:00+00:00")
    _landing(project, "ph-a")
    row = _row(build_phase_rows(tmp_path), "ph-a")
    assert row.elapsed_seconds == 6 * 3600
    assert "elapsed_seconds" not in row.missing


def test_null_with_reason_when_the_phase_has_no_landing_source(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    row = _row(build_phase_rows(tmp_path), "ph-a")
    assert row.landing_time is None
    assert row.landing_source is None
    assert row.missing["landing_time"]
    assert row.elapsed_seconds is None
    assert row.missing["elapsed_seconds"]


def test_null_with_reason_when_the_phase_has_no_specification(tmp_path: Path, clock: Clock) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    clock.at("2026-11-02T00:00:00+00:00")
    _landing(project, "ph-a")
    row = _row(build_phase_rows(tmp_path), "ph-a")
    assert row.landing_time == "2026-11-02T00:00:00+00:00"
    assert row.elapsed_seconds is None
    assert row.missing["elapsed_seconds"]
    assert "landing_time" not in row.missing


def test_null_with_reason_when_the_weight_is_unset(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef", weight=None)
    row = _row(build_phase_rows(tmp_path), "ph-a")
    assert row.weight is None
    assert row.missing["weight"]
