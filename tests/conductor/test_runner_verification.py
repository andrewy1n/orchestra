from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.project import Project
from orchestra.conductor.tasks import land_task, verification_run
from orchestra.conductor.tasks.close import task_close
from orchestra.conductor.verification.check import DEFAULT_TIMEOUT_S, CheckOutcome
from orchestra.tools import Git


def _world(
    tmp_path: Path, commands: tuple[str, ...] = ("true",)
) -> tuple[Project, land_task.LandedTask]:
    project = make_project(tmp_path)
    git = Git(tmp_path)
    git.run("config", "user.name", "Test")
    git.run("config", "user.email", "test@example.com")
    (tmp_path / ".gitignore").write_text(".canon/canon.db\n")
    (tmp_path / "base.txt").write_text("base\n")
    git.run("add", "-A")
    git.run("commit", "-qm", "base")
    create(project, "score:effort", "ef", {"goal": "Goal", "kind": "deliver"})
    create(project, "score:phase", "ph", {"title": "Phase", "ordinal": 1, "effort": "ef"})
    create(
        project,
        "score:specification",
        "ph",
        {"weight": "full", "phase": "ph", "effort": "ef", "requirements": ["R1"]},
    )
    create(
        project,
        "score:work-item",
        "implementation",
        {
            "title": "Implementation",
            "phase": "ph",
            "kind": "deliver",
            "assignee": "",
            "effort": "ef",
            "executor": "inline",
            "requirements": [],
        },
    )
    implementation = project.resolve("score:work-item", "implementation")
    project.update(implementation["id"], record_type="score:work-item", transition="in_progress")
    project.update(implementation["id"], record_type="score:work-item", transition="done")
    item = create(
        project,
        "score:work-item",
        "verify",
        {
            "title": "Verify",
            "phase": "ph",
            "kind": "deliver",
            "assignee": "",
            "effort": "ef",
            "executor": "subagent",
            "requirements": ["R1"],
            "depends_on": ["implementation"],
            "write_root": str(tmp_path),
        },
    )
    project.update(item["id"], record_type="score:work-item", transition="in_progress")
    for index, command in enumerate(commands):
        create(
            project,
            "score:acceptance",
            f"verify-{index}",
            {
                "method": "check",
                "phase": "ph",
                "effort": "ef",
                "verify_command": command,
                "requirement": "R1",
            },
        )
    head = git.head()
    report = create(
        project,
        "conductor:execution-report",
        "verify",
        {"work_item": "verify", "result": "pass", "verdict": "pass", "revision": head},
        "evidence: verification run",
    )
    landed = land_task.LandedTask(
        task="verify",
        phase="ph",
        commit="",
        revision=head,
        report_id=report["id"],
        checks=(),
        evidence_result="pass",
        verdict="pass",
    )
    return project, landed


def test_r4_closing_runner_checks_every_active_acceptance_in_stable_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, landed = _world(tmp_path, ("true", "true"))
    order: list[str] = []
    run_check = verification_run.run_check

    def record_order(
        *,
        acceptance_id: str,
        cwd: Path,
        project: Project,
        allow_dirty: bool = False,
        execution_report: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_S,
    ) -> CheckOutcome:
        order.append(acceptance_id)
        return run_check(
            acceptance_id=acceptance_id,
            cwd=cwd,
            project=project,
            allow_dirty=allow_dirty,
            execution_report=execution_report,
            timeout=timeout,
        )

    monkeypatch.setattr(verification_run, "run_check", record_order)

    closure = task_close.close(project, landed, frozenset())

    assert closure.state == "done", closure.reasons
    acceptances = sorted(project.list("score:acceptance"), key=lambda record: record["subject"])
    assert order == [record["id"] for record in acceptances]


def test_r8_task_without_runnable_acceptance_checks_stays_in_progress(
    tmp_path: Path,
) -> None:
    project, landed = _world(tmp_path, ())

    closure = task_close.close(project, landed, frozenset())

    assert closure.state == "in_progress"
    assert "no active acceptance checks" in closure.reasons
    assert project.resolve("score:work-item", "verify")["lifecycle_state"] == "in_progress"


def test_r5_closing_checks_keep_the_existing_tdd_red_gate(tmp_path: Path) -> None:
    project, landed = _world(tmp_path)
    acceptance = project.list("score:acceptance")[0]
    project.update(acceptance["id"], record_type="score:acceptance", payload={"method": "tdd"})

    closure = task_close.close(project, landed, frozenset())

    assert closure.state == "in_progress"
    assert any("red" in reason.lower() for reason in closure.reasons)
    assert project.resolve("score:work-item", "verify")["lifecycle_state"] == "in_progress"


def test_r6_failed_check_is_recorded_and_keeps_task_open(tmp_path: Path) -> None:
    project, landed = _world(tmp_path, ("false",))

    closure = task_close.close(project, landed, frozenset())

    assert closure.state == "in_progress"
    assert project.resolve("score:work-item", "verify")["lifecycle_state"] == "in_progress"
    check_runs = project.list("tuner:check-run")
    assert len(check_runs) == 1
    check_run = check_runs[0]
    assert check_run["payload"]["result"] == "fail"
    assert check_run["payload"]["exit_code"] != 0


def test_r7_unsigned_manual_acceptance_keeps_task_open(tmp_path: Path) -> None:
    project, landed = _world(tmp_path)
    acceptance = project.list("score:acceptance")[0]
    project.update(acceptance["id"], record_type="score:acceptance", payload={"method": "manual"})

    closure = task_close.close(project, landed, frozenset())

    assert closure.code == task_close.CODE_PENDING_HUMAN
    assert closure.state == "in_progress"
    assert project.list("tuner:check-run") == []


def test_r7_signed_manual_acceptance_uses_existing_human_evidence(tmp_path: Path) -> None:
    project, landed = _world(tmp_path)
    acceptance = project.list("score:acceptance")[0]
    project.update(acceptance["id"], record_type="score:acceptance", payload={"method": "manual"})
    create(
        project,
        "tuner:check-run",
        "verify",
        {
            "criterion_id": acceptance["id"],
            "revision": landed.revision,
            "result": "pass",
            "effort": "ef",
            "method": "manual",
            "signed_by": "reviewer",
            "informed_by": [acceptance["id"], landed.report_id],
        },
    )

    closure = task_close.close(project, landed, frozenset())

    assert closure.state == "done", closure.reasons


def test_r7_mixed_manual_and_command_checks_run_without_signing_manual(
    tmp_path: Path,
) -> None:
    project, landed = _world(tmp_path, ("true",))
    manual = create(
        project,
        "score:acceptance",
        "verify-manual",
        {
            "method": "manual",
            "phase": "ph",
            "effort": "ef",
            "verify_command": "true",
            "requirement": "R1",
        },
    )

    closure = task_close.close(project, landed, frozenset())

    assert closure.state == "in_progress"
    assert manual["id"]
    assert len(project.list("tuner:check-run")) == 1


def test_r9_closing_verification_refuses_untracked_source_changes(tmp_path: Path) -> None:
    project, landed = _world(tmp_path, ("touch runner-created.txt",))
    git = Git(tmp_path)
    before_head = git.head()
    before_status = git.run("status", "--porcelain", "--untracked-files=all").stdout

    closure = task_close.close(project, landed, frozenset())

    assert closure.state == "in_progress"
    assert git.head() == before_head
    assert (tmp_path / "runner-created.txt").is_file()
    assert git.run("status", "--porcelain", "--untracked-files=all").stdout != before_status


def test_r12_repeated_verification_reuses_check_run(tmp_path: Path) -> None:
    project, landed = _world(tmp_path)

    first = verification_run.run_closing_checks(project, landed)
    second = verification_run.run_closing_checks(project, landed)

    assert first.checks[0].check_run_id == second.checks[0].check_run_id
    assert len(project.list("tuner:check-run")) == 1


def test_interrupted_verification_resumes_at_remaining_acceptances(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, landed = _world(tmp_path, ("true", "true"))
    run_check = verification_run.run_check
    calls = 0

    def stop_after_first(
        *,
        acceptance_id: str,
        cwd: Path,
        project: Project,
        allow_dirty: bool = False,
        execution_report: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_S,
    ) -> CheckOutcome:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("interrupted")
        return run_check(
            acceptance_id=acceptance_id,
            cwd=cwd,
            project=project,
            allow_dirty=allow_dirty,
            execution_report=execution_report,
            timeout=timeout,
        )

    monkeypatch.setattr(verification_run, "run_check", stop_after_first)
    with pytest.raises(RuntimeError, match="interrupted"):
        verification_run.run_closing_checks(project, landed)
    monkeypatch.setattr(verification_run, "run_check", run_check)

    resumed = verification_run.run_closing_checks(project, landed)

    assert len(resumed.checks) == 2
    assert len(project.list("tuner:check-run")) == 2


def test_missing_runner_command_keeps_task_open(tmp_path: Path) -> None:
    project, landed = _world(tmp_path, ("orchestra-missing-command",))

    closure = task_close.close(project, landed, frozenset())

    assert closure.state == "in_progress"
    assert project.resolve("score:work-item", "verify")["lifecycle_state"] == "in_progress"
    assert project.list("tuner:check-run")[0]["payload"]["result"] == "blocked"


def test_runner_source_edit_refuses_closure(tmp_path: Path) -> None:
    project, landed = _world(tmp_path, ("printf changed >> base.txt",))

    closure = task_close.close(project, landed, frozenset())

    assert closure.state == "in_progress"
    assert "changed during closing verification" in closure.reasons[0]
    assert project.resolve("score:work-item", "verify")["lifecycle_state"] == "in_progress"
