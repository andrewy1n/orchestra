from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject
from orchestra.conductor import land_task
from orchestra.conductor.check import CheckOutcome
from orchestra.conductor.evidence import EvidenceError, parse_evidence
from orchestra.conductor.execution_cost import new_dispatch_markers

PHASE = "cost-phase"
EFFORT = "cost-effort"
PHASE_BODY = (
    "## Problem\n\nProblem.\n\n## Approach\n\nApproach.\n\n## Exit criteria\n\nCriteria.\n\n"
    "## Landing\n\nbranch: phase/cost-phase\nworktree: <repo>/.worktrees/cost-phase\nbase: main\n"
)
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


def _world(
    tmp_path: Path,
    *,
    verify_command: str = "true",
    dispatch_id: str | None = None,
    dispatched_at: str | None = None,
) -> tuple[Project, Path, Path]:
    project = make_project(tmp_path)
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "base.txt").write_text("base\n")
    _git(tmp_path, "add", "base.txt")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "Cost", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Execution cost", "ordinal": 1, "effort": EFFORT},
        PHASE_BODY,
    )
    _git(tmp_path, "branch", f"phase/{PHASE}", "main")
    worktrees = tmp_path / ".worktrees"
    worktrees.mkdir()
    phase_tree = worktrees / PHASE
    _git(tmp_path, "worktree", "add", "-q", str(phase_tree), f"phase/{PHASE}")
    item_payload: dict[str, object] = {
        "title": "Measure landing cost",
        "phase": PHASE,
        "kind": "deliver",
        "assignee": "",
        "effort": EFFORT,
        "executor": "inline",
        "requirements": ["R1"],
    }
    if dispatch_id is not None:
        item_payload["dispatch_id"] = dispatch_id
    if dispatched_at is not None:
        item_payload["dispatched_at"] = dispatched_at
    create(
        project,
        "score:work-item",
        "cost-task",
        item_payload,
        "## Description\n\nMeasure landing cost.\n\n## Approach\n\nDo it.",
    )
    create(
        project,
        "score:acceptance",
        "cost-task",
        {
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": verify_command,
            "requirement": "R1",
        },
    )
    tree = worktrees / f"{PHASE}--cost-task"
    _git(tmp_path, "branch", f"task/{PHASE}/cost-task", f"phase/{PHASE}")
    _git(tmp_path, "worktree", "add", "-q", str(tree), f"task/{PHASE}/cost-task")
    item = project.resolve("score:work-item", "cost-task")
    project.update(
        item["id"],
        record_type="score:work-item",
        transition="in_progress",
        payload={"assignee": "inline", "write_root": str(tree)},
    )
    return project, tmp_path, tree


def _evidence_file(tmp_path: Path, **override: object) -> Path:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({**EVIDENCE, **override}))
    return path


def _report(project: Project, report_id: str) -> JsonObject:
    return project.get(report_id, "conductor:execution-report")["payload"]


def test_r2_elapsed_duration_covers_dispatch_through_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo, _ = _world(tmp_path, dispatch_id="dispatch-1", dispatched_at=START.isoformat())
    receipt = START + timedelta(seconds=25.75)
    monkeypatch.setattr(land_task, "utc_now", lambda: receipt)

    landed = land_task.land(project, repo, "cost-task", _evidence_file(tmp_path))

    payload = _report(project, landed.report_id)
    assert payload["dispatch_id"] == "dispatch-1"
    assert payload["duration_s"] == 25.75


def test_dispatch_markers_have_a_unique_id_and_utc_start() -> None:
    first = new_dispatch_markers(START)
    second = new_dispatch_markers(START)

    assert first.dispatch_id
    assert first.dispatch_id != second.dispatch_id
    assert datetime.fromisoformat(first.dispatched_at) == START
    assert datetime.fromisoformat(first.dispatched_at).utcoffset() == timedelta(0)


def test_r3_check_delay_is_excluded_from_elapsed_duration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo, _ = _world(tmp_path, dispatch_id="dispatch-1", dispatched_at=START.isoformat())
    receipt = START + timedelta(seconds=7)
    clock = [receipt]

    def run_check(**_: object) -> CheckOutcome:
        clock[0] += timedelta(hours=1)
        return CheckOutcome(exit_code=0, stdout="")

    monkeypatch.setattr(land_task, "utc_now", lambda: clock[0])
    monkeypatch.setattr(land_task, "run_check", run_check)

    landed = land_task.land(project, repo, "cost-task", _evidence_file(tmp_path))

    assert _report(project, landed.report_id)["duration_s"] == 7


def test_r5_landing_preserves_reported_tokens_total(tmp_path: Path) -> None:
    project, repo, _ = _world(tmp_path)

    landed = land_task.land(project, repo, "cost-task", _evidence_file(tmp_path, tokens_total=1234))

    assert _report(project, landed.report_id)["tokens_total"] == 1234


@pytest.mark.parametrize(
    ("evidence", "expected"),
    [({}, None), ({"tokens_total": 0}, 0)],
)
def test_r6_missing_or_zero_token_count_is_preserved(
    tmp_path: Path, evidence: dict[str, object], expected: int | None
) -> None:
    project, repo, _ = _world(tmp_path)

    landed = land_task.land(project, repo, "cost-task", _evidence_file(tmp_path, **evidence))

    payload = _report(project, landed.report_id)
    if expected is None:
        assert "tokens_total" not in payload
    else:
        assert payload["tokens_total"] == expected


def test_r6_missing_dispatch_metadata_leaves_duration_absent(tmp_path: Path) -> None:
    project, repo, _ = _world(tmp_path, dispatch_id=None, dispatched_at=None)

    landed = land_task.land(project, repo, "cost-task", _evidence_file(tmp_path))

    payload = _report(project, landed.report_id)
    assert "dispatch_id" not in payload
    assert "duration_s" not in payload


@pytest.mark.parametrize(
    "tokens_total",
    [-1, 1.5, True, float("inf"), float("nan")],
)
def test_r7_invalid_token_count_fails_before_landing_changes_git_or_writes_evidence(
    tmp_path: Path, tokens_total: object
) -> None:
    project, repo, tree = _world(tmp_path)
    (tree / "work.txt").write_text("work\n")
    head_before = _git(tree, "rev-parse", "HEAD")
    path = _evidence_file(tmp_path, tokens_total=tokens_total)

    with pytest.raises(EvidenceError):
        land_task.land(project, repo, "cost-task", path)

    assert _git(tree, "rev-parse", "HEAD") == head_before
    assert project.list("conductor:execution-report") == []
    assert project.list("tuner:check-run") == []
    assert project.resolve("score:work-item", "cost-task")["lifecycle_state"] == "in_progress"


@pytest.mark.parametrize(
    "dispatched_at",
    ["not-a-timestamp", "2026-01-01T00:00:00", "2026-01-01T01:00:00+01:00"],
)
def test_r7_invalid_dispatch_timestamp_fails_before_landing_changes_git_or_writes_evidence(
    tmp_path: Path, dispatched_at: str
) -> None:
    project, repo, tree = _world(tmp_path, dispatch_id="dispatch-1", dispatched_at=dispatched_at)
    (tree / "work.txt").write_text("work\n")
    head_before = _git(tree, "rev-parse", "HEAD")

    with pytest.raises(land_task.LandError):
        land_task.land(project, repo, "cost-task", _evidence_file(tmp_path))

    assert _git(tree, "rev-parse", "HEAD") == head_before
    assert project.list("conductor:execution-report") == []
    assert project.list("tuner:check-run") == []


def test_r7_partial_dispatch_fields_fail_before_landing_changes_git_or_writes_evidence(
    tmp_path: Path,
) -> None:
    project, repo, tree = _world(tmp_path, dispatch_id="dispatch-1", dispatched_at=None)
    (tree / "work.txt").write_text("work\n")
    head_before = _git(tree, "rev-parse", "HEAD")

    with pytest.raises(land_task.LandError):
        land_task.land(project, repo, "cost-task", _evidence_file(tmp_path))

    assert _git(tree, "rev-parse", "HEAD") == head_before
    assert project.list("conductor:execution-report") == []
    assert project.list("tuner:check-run") == []


def test_r7_negative_elapsed_interval_fails_before_landing_changes_git_or_writes_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo, tree = _world(
        tmp_path, dispatch_id="dispatch-1", dispatched_at=START.isoformat()
    )
    monkeypatch.setattr(land_task, "utc_now", lambda: START - timedelta(seconds=1))
    (tree / "work.txt").write_text("work\n")
    head_before = _git(tree, "rev-parse", "HEAD")

    with pytest.raises(land_task.LandError):
        land_task.land(project, repo, "cost-task", _evidence_file(tmp_path))

    assert _git(tree, "rev-parse", "HEAD") == head_before
    assert project.list("conductor:execution-report") == []
    assert project.list("tuner:check-run") == []


def test_r7_invalid_executor_duration_is_rejected(tmp_path: Path) -> None:
    path = _evidence_file(tmp_path, duration_s=0)

    with pytest.raises(EvidenceError, match="duration_s"):
        parse_evidence(path)


def test_r9_legacy_evidence_without_tokens_remains_valid(tmp_path: Path) -> None:
    project, repo, _ = _world(tmp_path)

    landed = land_task.land(project, repo, "cost-task", _evidence_file(tmp_path))

    assert "tokens_total" not in _report(project, landed.report_id)


def test_duplicate_landing_does_not_increase_duration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo, _ = _world(tmp_path, dispatch_id="dispatch-1", dispatched_at=START.isoformat())
    receipts = iter((START + timedelta(seconds=10), START + timedelta(seconds=30)))
    monkeypatch.setattr(land_task, "utc_now", lambda: next(receipts))
    evidence_path = _evidence_file(tmp_path)

    first = land_task.land(project, repo, "cost-task", evidence_path)
    second = land_task.land(project, repo, "cost-task", evidence_path)

    assert first.report_id == second.report_id
    assert _report(project, first.report_id)["duration_s"] == 10


def test_r10_legacy_report_without_cost_fields_remains_valid(tmp_path: Path) -> None:
    project, repo, _ = _world(tmp_path, dispatch_id=None, dispatched_at=None)
    item = project.resolve("score:work-item", "cost-task")

    report = project.create(
        record_type="conductor:execution-report",
        subject="legacy-report",
        payload={
            "work_item": item["subject"],
            "result": "pass",
            "verdict": "pass",
            "revision": _git(repo, "rev-parse", "HEAD"),
        },
        body="",
    )

    assert "duration_s" not in report["payload"]
    assert "dispatch_id" not in report["payload"]
    assert "tokens_total" not in report["payload"]
