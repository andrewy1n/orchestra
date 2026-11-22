from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.project import Project, open_store
from orchestra.conductor import gate, wave
from orchestra.conductor.phase_progress import _gates
from orchestra.score.phase import read_phase
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


def _task(project: Project, phase: str, slug: str = "", *, needs: tuple[str, ...] = ()) -> None:
    create(
        project,
        "score:work-item",
        slug or f"task-{phase}",
        {
            "title": "Work",
            "phase": phase,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
            "depends_on": list(needs),
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


def test_task_question_holds_its_dependency_chain_and_phase_close(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _phase(project, "one", 1)
    _task(project, "one", "hold")
    _task(project, "one", "dependent", needs=("hold",))
    _task(project, "one", "independent")
    task = project.resolve("score:work-item", "hold")
    task = project.update(task["id"], transition="in_progress")
    project.update(task["id"], transition="done")
    question = create(
        project,
        "score:continuity-question",
        EFFORT,
        {"owner": "user", "blocking": True, "phase": "one", "scope": "task:hold"},
    )

    assert [task.task for task in wave.start(project, repo, "one").tasks] == ["independent"]
    assert any(
        not term.holds and term.detail == "task:hold"
        for term in gate.gate_terms(open_store(repo), "one")
    )

    project.update(question["id"], transition="answered")
    assert [task.task for task in wave.start(project, repo, "one").tasks] == ["dependent"]


def test_task_question_reports_a_task_in_the_wrong_phase(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _phase(project, "one", 1)
    _phase(project, "two", 2)
    _task(project, "one")
    _task(project, "two")
    create(
        project,
        "score:continuity-question",
        EFFORT,
        {"owner": "user", "blocking": True, "phase": "one", "scope": "task:task-two"},
    )

    with pytest.raises(wave.WaveError, match="holds unknown task 'task-two' in phase 'one'"):
        wave.start(project, repo, "one")
    assert [task.task for task in wave.start(project, repo, "two").tasks] == ["task-two"]


def test_task_question_reports_a_missing_phase(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _phase(project, "one", 1)
    _task(project, "one")
    create(
        project,
        "score:continuity-question",
        EFFORT,
        {"owner": "user", "blocking": True, "scope": "task:task-one"},
    )

    with pytest.raises(wave.WaveError, match="needs a phase for task 'task-one'"):
        wave.start(project, repo, "one")


def test_phase_owned_finding_blocks_only_its_phase(tmp_path: Path) -> None:
    project, store = _repo(tmp_path)
    _phase(project, "one", 1)
    _phase(project, "two", 2)
    _finding(project, "phase-question", phase="one")

    one = {term.name for term in gate.gate_terms(open_store(store), "one") if not term.holds}
    two = {term.name for term in gate.gate_terms(open_store(store), "two") if not term.holds}

    assert "finding-needs-human:phase-question" in one
    assert "finding-needs-human:phase-question" not in two
    assert [item.record["subject"] for item in phase_blockers(project.records(), "two")] == []


def test_r9_blocking_question_stays_ahead_of_a_later_finding(tmp_path: Path) -> None:
    project, _store = _repo(tmp_path)
    _phase(project, "one", 1)
    create(
        project,
        "score:continuity-question",
        EFFORT,
        {"owner": "user", "blocking": True, "phase": "one", "scope": "all"},
    )
    _finding(project, "later-finding", phase="one")
    records = project.records()

    assert [item.record["subject"] for item in phase_blockers(records, "one")] == [
        EFFORT,
        "later-finding",
    ]
    phase = read_phase(
        next(
            record
            for record in records
            if record["record_type"] == "score:phase" and record["subject"] == "one"
        )
    )
    text = "human gate: " + ", ".join(item.subject for item in _gates(records, phase))
    assert text == "human gate: blocker-effort, later-finding"


def test_unscoped_finding_blocks_entire_effort(tmp_path: Path) -> None:
    project, store = _repo(tmp_path)
    _phase(project, "one", 1)
    _phase(project, "two", 2)
    _finding(project, "effort-question")

    for phase in ("one", "two"):
        assert "finding-needs-human:effort-question" in {
            term.name for term in gate.gate_terms(open_store(store), phase) if not term.holds
        }
        assert [item.record["subject"] for item in phase_blockers(project.records(), phase)] == [
            "effort-question"
        ]
