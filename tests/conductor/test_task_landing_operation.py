from __future__ import annotations

from pathlib import Path

import pytest
from test_task_land import _evidence_file, _git
from test_task_land_close import _state, _world

from orchestra.canon.project import Project
from orchestra.conductor.tasks import land_task
from orchestra.conductor.tasks.close.task_close import CODE_DONE, CODE_FAILED, CODE_PENDING_HUMAN
from orchestra.conductor.tasks.task_landing import TaskLanding, land_and_close
from orchestra.conductor.verification import verification


def _land(project: Project, repo: Path, tmp_path: Path, **evidence: object) -> TaskLanding:
    return land_and_close(project, repo, "a", _evidence_file(tmp_path, **evidence))


def _tree(project: Project) -> Path:
    return Path(str(project.resolve("score:work-item", "a")["payload"]["write_root"]))


def _make_closing_task(project: Project) -> None:
    from canon_support import create

    create(
        project,
        "score:work-item",
        "impl",
        {
            "title": "impl",
            "phase": "ph",
            "kind": "deliver",
            "assignee": "",
            "effort": "ef",
            "executor": "inline",
            "requirements": [],
        },
    )
    impl = project.resolve("score:work-item", "impl")
    project.update(impl["id"], record_type="score:work-item", transition="in_progress")
    project.update(impl["id"], record_type="score:work-item", transition="done")
    item = project.resolve("score:work-item", "a")
    project.update(item["id"], record_type="score:work-item", payload={"depends_on": ["impl"]})


def test_r1_closes_the_task_when_evidence_and_checks_pass(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    landing = _land(project, repo, tmp_path)
    assert landing.closure.state == "done"
    assert landing.closure.code == CODE_DONE
    assert landing.closure.reasons == ()
    assert [c.exit_code for c in landing.landed.checks] == [0]
    assert _state(project) == "done"


def test_r1_returns_the_landed_task_alongside_the_closure(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    landing = _land(project, repo, tmp_path)
    assert landing.landed.task == "a"
    assert landing.landed.report_id
    assert landing.landed.revision == _git(_tree(project), "rev-parse", "HEAD")


def test_r1_refuses_a_task_that_is_not_in_progress(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    _land(project, repo, tmp_path)
    with pytest.raises(land_task.LandError, match="no in_progress work-item 'a'"):
        _land(project, repo, tmp_path)


def test_landing_refuses_held_work_before_committing_or_recording_evidence(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    tree = _tree(project)
    head = _git(tree, "rev-parse", "HEAD")
    (tree / "held.txt").write_text("pending\n")
    project.create(
        record_type="score:continuity-question",
        subject="ef",
        payload={"owner": "user", "blocking": True, "phase": "ph", "scope": "task:a"},
    )

    with pytest.raises(land_task.LandError, match="task 'a' is blocked"):
        _land(project, repo, tmp_path)

    assert _git(tree, "rev-parse", "HEAD") == head
    assert not project.list("conductor:execution-report")


def test_r2_keeps_the_task_in_progress_when_evidence_fails(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    landing = _land(project, repo, tmp_path, result="fail", verdict="fail")
    assert landing.closure.state == "in_progress"
    assert landing.closure.code == CODE_FAILED
    assert "evidence result is fail" in landing.closure.reasons
    assert _state(project) == "in_progress"


def test_r2_keeps_the_task_in_progress_when_a_check_fails(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"verify_command": "false"})
    landing = _land(project, repo, tmp_path)
    assert landing.closure.state == "in_progress"
    assert landing.closure.code == CODE_FAILED
    assert [c.exit_code for c in landing.landed.checks] != [0]
    assert _state(project) == "in_progress"


def test_r2_keeps_the_task_in_progress_when_a_requirement_is_unverified(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"requirement": "R9"})
    landing = _land(project, repo, tmp_path)
    assert landing.closure.state == "in_progress"
    assert landing.closure.code == CODE_FAILED
    assert landing.closure.reasons == ("requirements not verified: R1",)
    assert _state(project) == "in_progress"


def test_r3_keeps_the_task_in_progress_for_a_manual_acceptance(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"method": "manual"})
    landing = _land(project, repo, tmp_path)
    assert landing.closure.state == "in_progress"
    assert landing.closure.code == CODE_PENDING_HUMAN
    assert _state(project) == "in_progress"


def test_r3_keeps_the_task_in_progress_for_a_needs_human_report(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    landing = _land(project, repo, tmp_path, verdict="inconclusive", needs_human=True)
    assert landing.closure.state == "in_progress"
    assert landing.closure.code == CODE_PENDING_HUMAN
    assert landing.landed.needs_human
    assert _state(project) == "in_progress"


def test_r4_opens_a_blocking_question_for_a_needs_human_report(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    landing = _land(project, repo, tmp_path, verdict="inconclusive", needs_human=True)
    assert landing.closure.question_id
    question = project.get(landing.closure.question_id, "score:continuity-question")
    assert question["payload"]["scope"] == "human:a"


def test_r4_opens_no_question_when_nothing_needs_a_human(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    landing = _land(project, repo, tmp_path)
    assert landing.closure.question_id == ""
    assert project.list("score:continuity-question") == []


def test_r15_a_closing_task_makes_no_task_commit(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    _make_closing_task(project)
    tree = _tree(project)
    head = _git(tree, "rev-parse", "HEAD")
    (tree / "work.txt").write_text("work\n")
    landing = _land(project, repo, tmp_path)
    assert landing.landed.commit == ""
    assert landing.landed.revision == head
    assert _git(tree, "rev-parse", "HEAD") == head
    assert landing.closure.state == "in_progress"


def test_r15_a_closing_task_runs_phase_closing_checks_before_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo = _world(tmp_path)
    _make_closing_task(project)
    states: list[str] = []
    real = verification.run_closing_checks

    def spy(asked: Project, landed: land_task.LandedTask) -> verification.VerificationRun:
        states.append(_state(asked))
        return real(asked, landed)

    monkeypatch.setattr(verification, "run_closing_checks", spy)
    landing = _land(project, repo, tmp_path)
    assert states == ["in_progress"]
    assert landing.closure.state == "done"
    assert _state(project) == "done"
