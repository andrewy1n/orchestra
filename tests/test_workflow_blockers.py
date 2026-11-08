from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.project import Project
from orchestra.conductor import gate, wave
from orchestra.score.workflow_blockers import phase_blockers

EFFORT = "blocker-effort"


def _phase(project: Project, slug: str, ordinal: int, **extra: object) -> None:
    create(
        project,
        "score:phase",
        slug,
        {"title": slug, "ordinal": ordinal, "effort": EFFORT, **extra},
    )


def _finding(project: Project, subject: str, *, phase: str | None = None) -> None:
    payload: dict[str, object] = {
        "claim": "A human decision is required.",
        "basis": "Evidence",
        "invalidated_when": "A human resolves it.",
        "effort": EFFORT,
        "needs": "human",
    }
    if phase is not None:
        payload["phase"] = phase
    create(project, "tuner:finding", subject, payload)


def _task(project: Project, phase: str) -> None:
    create(
        project,
        "score:work-item",
        f"task-{phase}",
        {
            "title": "Work",
            "phase": phase,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
        },
    )


def _repo(tmp_path: Path) -> tuple[Project, Path]:
    project = make_project(tmp_path)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"], check=True
    )
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test"], check=True)
    (tmp_path / "orchestra.toml").write_text(
        '[verify.stages]\ntask = ["unit"]\n\n'
        '[verify.unit]\nrunner = ["python", "-m", "pytest", "{tests}", "--junitxml={report}"]\n\n'
        '[suite]\nmode = "none"\ngate = "required"\n'
    )
    create(project, "score:effort", EFFORT, {"goal": "Goal", "kind": "deliver"})
    return project, tmp_path


def test_independent_phase_remains_runnable(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _phase(project, "blocked", 1)
    _phase(project, "independent", 2)
    _finding(project, "needs-answer", phase="blocked")
    _task(project, "blocked")
    _task(project, "independent")

    with pytest.raises(wave.WaveError, match="blocked"):
        wave.start(project, repo, "blocked")
    started = wave.start(project, repo, "independent")

    assert [task.task for task in started.tasks] == ["task-independent"]


def test_dependent_phase_waits_for_blocked_prerequisite(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _phase(project, "blocked", 1)
    _phase(project, "independent", 2)
    _phase(project, "dependent", 3, depends_on=["blocked"])
    _finding(project, "needs-answer", phase="blocked")
    for phase in ("blocked", "independent", "dependent"):
        _task(project, phase)

    assert [task.task for task in wave.start(project, repo, "independent").tasks] == [
        "task-independent"
    ]
    with pytest.raises(wave.WaveError, match="needs-answer"):
        wave.start(project, repo, "dependent")


def test_phase_owned_finding_blocks_only_its_phase(tmp_path: Path) -> None:
    project, store = _repo(tmp_path)
    _phase(project, "one", 1)
    _phase(project, "two", 2)
    _finding(project, "phase-question", phase="one")

    one = {term.name for term in gate.gate_terms(store, "one") if not term.holds}
    two = {term.name for term in gate.gate_terms(store, "two") if not term.holds}

    assert "finding-needs-human:phase-question" in one
    assert "finding-needs-human:phase-question" not in two
    assert [item.record["subject"] for item in phase_blockers(project.records(), "two")] == []


def test_unscoped_finding_blocks_entire_effort(tmp_path: Path) -> None:
    project, store = _repo(tmp_path)
    _phase(project, "one", 1)
    _phase(project, "two", 2)
    _finding(project, "effort-question")

    for phase in ("one", "two"):
        assert "finding-needs-human:effort-question" in {
            term.name for term in gate.gate_terms(store, phase) if not term.holds
        }
        assert [item.record["subject"] for item in phase_blockers(project.records(), phase)] == [
            "effort-question"
        ]
