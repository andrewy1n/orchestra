from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.conductor.tasks.resume.task_resume import ResumeError, resume

PHASE = "resume-phase"
EFFORT = "resume-effort"
TASK = "task"
BODY = "## Problem\n\nProblem.\n\n## Approach\n\nApproach.\n\n## Exit criteria\n\nCriteria."


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def _commit(root: Path, name: str) -> str:
    (root / name).write_text(name)
    _git(root, "add", name)
    _git(root, "commit", "-q", "-m", name)
    return _git(root, "rev-parse", "HEAD")


def _world(tmp_path: Path, *, dispatch_id: str = "dispatch-1") -> Project:
    project = make_project(tmp_path)
    exclude = tmp_path / ".git" / "info" / "exclude"
    exclude.write_text(exclude.read_text() + "\n.canon/\n")
    _git(tmp_path, "commit", "-q", "--allow-empty", "-m", "base")
    _git(tmp_path, "branch", f"phase/{PHASE}")
    create(project, "score:effort", EFFORT, {"goal": "Resume", "kind": "deliver"})
    create(project, "score:phase", PHASE, {"title": "Resume", "ordinal": 1, "effort": EFFORT}, BODY)
    create(
        project,
        "score:work-item",
        TASK,
        {
            "title": TASK,
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "subagent",
            "effort": EFFORT,
            "write_root": str(tmp_path),
            "dispatch_id": dispatch_id,
            "dispatch_started_at": "2026-01-01T00:00:00Z",
            "attempts": 1,
        },
        "## Description\n\nDo it.\n\n## Approach\n\nJust do it.",
    )
    item = project.resolve("score:work-item", TASK)
    project.update(item["id"], record_type="score:work-item", transition="in_progress")
    return project


def _acceptance(project: Project, subject: str) -> str:
    record = create(
        project,
        "score:acceptance",
        subject,
        {
            "method": "check",
            "oracle_policy": "none",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    return record["id"]


def _pass_at(project: Project, acceptance_id: str, revision: str) -> None:
    create(
        project,
        "tuner:check-run",
        TASK,
        {
            "criterion_id": acceptance_id,
            "result": "pass",
            "method": "check",
            "effort": EFFORT,
            "revision": revision,
            "runner": "orchestra",
            "signed_by": "",
        },
    )


def _idle(_: Path) -> list[str]:
    return []


def test_resume_names_implement_when_the_worktree_has_no_work(tmp_path: Path) -> None:
    project = _world(tmp_path)
    report = resume(project, TASK, list_processes=_idle)
    assert report.step == "implement"
    assert report.commits_ahead == 0
    assert report.dirty is False


def test_resume_names_land_when_the_worktree_has_uncommitted_work(tmp_path: Path) -> None:
    project = _world(tmp_path)
    (tmp_path / "wip.txt").write_text("wip")
    report = resume(project, TASK, list_processes=_idle)
    assert report.step == "land"
    assert report.dirty is True


def test_resume_names_check_when_a_committed_acceptance_has_no_check_run_at_head(
    tmp_path: Path,
) -> None:
    project = _world(tmp_path)
    acceptance = _acceptance(project, TASK)
    _commit(tmp_path, "work.txt")
    report = resume(project, TASK, list_processes=_idle)
    assert report.step == "check"
    assert report.commits_ahead == 1
    assert report.pending_acceptances == (acceptance,)


def test_resume_names_check_when_the_only_check_run_is_at_an_older_revision(
    tmp_path: Path,
) -> None:
    project = _world(tmp_path)
    acceptance = _acceptance(project, TASK)
    older = _commit(tmp_path, "first.txt")
    _pass_at(project, acceptance, older)
    _commit(tmp_path, "second.txt")
    report = resume(project, TASK, list_processes=_idle)
    assert report.step == "check"
    assert report.pending_acceptances == (acceptance,)


def test_resume_names_close_when_every_acceptance_passed_at_head(tmp_path: Path) -> None:
    project = _world(tmp_path)
    acceptance = _acceptance(project, TASK)
    head = _commit(tmp_path, "work.txt")
    _pass_at(project, acceptance, head)
    report = resume(project, TASK, list_processes=_idle)
    assert report.step == "close"
    assert report.pending_acceptances == ()


def test_resume_refuses_when_a_process_holds_the_worktree(tmp_path: Path) -> None:
    project = _world(tmp_path)
    with pytest.raises(ResumeError, match="holds"):
        resume(project, TASK, list_processes=lambda _: ["claude (pid 4242)"])


def test_resume_refuses_when_an_execution_report_exists_for_the_dispatch(tmp_path: Path) -> None:
    project = _world(tmp_path)
    create(
        project,
        "conductor:execution-report",
        TASK,
        {
            "work_item": TASK,
            "result": "pass",
            "verdict": "pass",
            "revision": "abc123",
            "dispatch_id": "dispatch-1",
        },
        "## Evidence\n\nDone.",
    )
    with pytest.raises(ResumeError, match="execution report"):
        resume(project, TASK, list_processes=_idle)


def test_resume_refuses_when_the_process_lister_fails(tmp_path: Path) -> None:
    project = _world(tmp_path)

    def broken(_: Path) -> list[str]:
        raise OSError("lsof not found")

    with pytest.raises(ResumeError, match="cannot prove"):
        resume(project, TASK, list_processes=broken)


def test_resume_refuses_a_task_that_is_not_in_progress(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", EFFORT, {"goal": "Resume", "kind": "deliver"})
    create(project, "score:phase", PHASE, {"title": "Resume", "ordinal": 1, "effort": EFFORT}, BODY)
    create(
        project,
        "score:work-item",
        TASK,
        {"title": TASK, "phase": PHASE, "kind": "deliver", "assignee": "", "effort": EFFORT},
        "## Description\n\nDo it.\n\n## Approach\n\nJust do it.",
    )
    with pytest.raises(ResumeError, match="in_progress"):
        resume(project, TASK, list_processes=_idle)


def test_resume_leaves_attempts_unchanged(tmp_path: Path) -> None:
    project = _world(tmp_path)
    before = record_payload(project.resolve("score:work-item", TASK))
    resume(project, TASK, list_processes=_idle)
    after = record_payload(project.resolve("score:work-item", TASK))
    assert after["attempts"] == before["attempts"] == 1
    assert after["dispatch_id"] == before["dispatch_id"]
