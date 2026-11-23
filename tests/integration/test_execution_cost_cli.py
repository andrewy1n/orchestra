from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.project import Project
from orchestra.cli import main as cli_main
from orchestra.conductor.tasks import execution_cost, land_task

PHASE = "cost-phase"
EFFORT = "cost-effort"
START = datetime(2026, 1, 1, tzinfo=timezone.utc)
EVIDENCE = {
    "subject": "cost-task",
    "kind": "deliver",
    "result": "pass",
    "verdict": "pass",
    "evidence": "Acceptance passed.",
}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _world(root: Path) -> tuple[Project, Path, Path]:
    project = make_project(root)
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    (root / "base.txt").write_text("base\n")
    _git(root, "add", "base.txt")
    _git(root, "commit", "-qm", "base")
    _git(root, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "Cost", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Execution cost", "ordinal": 1, "effort": EFFORT},
        "## Problem\n\nProblem.\n\n## Approach\n\nApproach.\n\n"
        "## Exit criteria\n\nCriteria.\n\n## Landing\n\n"
        "branch: phase/cost-phase\nbase: main\n",
    )
    _git(root, "branch", f"phase/{PHASE}", "main")
    worktrees = root / ".worktrees"
    worktrees.mkdir()
    phase_tree = worktrees / PHASE
    _git(root, "worktree", "add", "-q", str(phase_tree), f"phase/{PHASE}")
    create(
        project,
        "score:work-item",
        "cost-task",
        {
            "title": "Measure dispatch cost",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
            "requirements": ["R1"],
        },
        "## Description\n\nMeasure dispatch cost.\n\n## Approach\n\nDo it.",
    )
    create(
        project,
        "score:acceptance",
        "cost-task",
        {
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    evidence_path = root / "evidence.json"
    return project, root, evidence_path


def _invoke(
    root: Path, args: list[str], capsys: pytest.CaptureFixture[str]
) -> tuple[int, str, str]:
    argv = [*args, "--cwd", str(root), "--store", str(root), "--json"]
    try:
        code = cli_main(argv)
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 1
    output = capsys.readouterr()
    return code, output.out, output.err


def _evidence(path: Path, *, result: str, verdict: str) -> None:
    path.write_text(json.dumps({**EVIDENCE, "result": result, "verdict": verdict}))


def test_cli_start_landing_redispatch_and_second_landing_keep_dispatches_distinct(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, repo, evidence_path = _world(tmp_path)
    clock = [START]
    monkeypatch.setattr(execution_cost, "utc_now", lambda: clock[0])
    monkeypatch.setattr(land_task, "utc_now", lambda: clock[0])

    code, output, error = _invoke(repo, ["wave", "start", PHASE], capsys)

    assert code == 0, error
    task = project.resolve("score:work-item", "cost-task")
    first_dispatch = task["payload"]["dispatch_id"]
    assert task["lifecycle_state"] == "in_progress"
    assert task["payload"]["dispatch_started_at"] == START.isoformat(timespec="microseconds")
    assert json.loads(output)["tasks"][0]["task"] == "cost-task"

    clock[0] += timedelta(seconds=12)
    _evidence(evidence_path, result="fail", verdict="fail")
    code, _, error = _invoke(
        repo,
        ["task", "land", "cost-task", "--evidence", str(evidence_path)],
        capsys,
    )
    assert code == 1, error
    first_report = project.list("conductor:execution-report")[-1]
    assert first_report["payload"]["dispatch_id"] == first_dispatch
    assert first_report["payload"]["duration_s"] == 12
    task = project.resolve("score:work-item", "cost-task")
    assert task["lifecycle_state"] == "in_progress"

    clock[0] += timedelta(seconds=1)
    code, output, error = _invoke(
        repo,
        [
            "task",
            "redispatch",
            "cost-task",
            "--expected-revision",
            task["revision"],
        ],
        capsys,
    )
    assert code == 0, error
    retried = project.resolve("score:work-item", "cost-task")
    second_dispatch = retried["payload"]["dispatch_id"]
    assert second_dispatch != first_dispatch
    assert retried["payload"]["attempts"] == 1
    assert json.loads(output)["dispatch_id"] == second_dispatch

    clock[0] += timedelta(seconds=20)
    _evidence(evidence_path, result="pass", verdict="pass")
    code, _, error = _invoke(
        repo,
        ["task", "land", "cost-task", "--evidence", str(evidence_path)],
        capsys,
    )
    assert code == 0, error
    reports = project.list("conductor:execution-report")
    assert len(reports) == 2
    reports_by_dispatch = {report["payload"]["dispatch_id"]: report for report in reports}
    assert reports_by_dispatch[first_dispatch]["payload"]["duration_s"] == 12
    assert reports_by_dispatch[second_dispatch]["payload"]["duration_s"] == 20


def test_cli_redispatch_refuses_stale_revision_without_changing_markers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, repo, _ = _world(tmp_path)
    monkeypatch.setattr(execution_cost, "utc_now", lambda: START)
    code, _, error = _invoke(repo, ["wave", "start", PHASE], capsys)
    assert code == 0, error
    task = project.resolve("score:work-item", "cost-task")
    stale_revision = task["revision"]
    project.update(task["id"], record_type="score:work-item", payload={"attempts": 0})
    changed = project.resolve("score:work-item", "cost-task")

    code, _, error = _invoke(
        repo,
        [
            "task",
            "redispatch",
            "cost-task",
            "--expected-revision",
            stale_revision,
        ],
        capsys,
    )

    assert code == 2
    assert "revision" in error.lower() or "stale" in error.lower()
    assert project.get(changed["id"])["payload"] == changed["payload"]
