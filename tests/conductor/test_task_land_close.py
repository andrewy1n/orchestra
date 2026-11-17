from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from canon_support import REPO, create, make_project

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject
from orchestra.conductor import land_task, task_close
from orchestra.conductor.task_close import CloseApproval, CloseRefusal, CriterionRequest

PHASE = "ph"
EFFORT = "ef"
PHASE_BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n"
    "## Landing\n\nbranch: phase/ph\nworktree: <repo>/.worktrees/ph\nbase: main\n"
)
SPEC_BODY = (
    "## Requirements\n\nR1: It works.\n\n## Acceptance criteria\n\nx\n\n## Constraints\n\nx\n\n"
    "## Non-goals\n\nx\n\n## Invariants\n\nx\n\n## Assumptions\n\nx"
)
EVIDENCE = {
    "subject": "a",
    "kind": "deliver",
    "result": "pass",
    "verdict": "pass",
    "evidence": "ran the acceptance",
}


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True)


def _world(tmp_path: Path, acceptance: JsonObject | None = None) -> tuple[Project, Path]:
    from orchestra.conductor import wave

    project = make_project(tmp_path)
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "base.txt").write_text("base\n")
    _git(tmp_path, "add", "base.txt")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    create(
        project, "score:phase", PHASE, {"title": "Ph", "ordinal": 1, "effort": EFFORT}, PHASE_BODY
    )
    create(
        project,
        "score:specification",
        PHASE,
        {"weight": "full", "phase": PHASE, "effort": EFFORT, "requirements": ["R1"]},
        SPEC_BODY,
    )
    _git(tmp_path, "branch", f"phase/{PHASE}", "main")
    (tmp_path / ".worktrees").mkdir()
    _git(tmp_path, "worktree", "add", "-q", str(tmp_path / ".worktrees" / PHASE), f"phase/{PHASE}")
    create(
        project,
        "score:work-item",
        "a",
        {
            "title": "a",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
            "requirements": ["R1"],
        },
        "## Description\n\nR1: It works.\n\n## Approach\n\nDo it.",
    )
    payload: JsonObject = {
        "method": "check",
        "phase": PHASE,
        "effort": EFFORT,
        "verify_command": "true",
        "requirement": "R1",
    }
    payload.update(acceptance or {})
    create(project, "score:acceptance", "a", payload)
    wave.start(project, tmp_path, PHASE)
    return project, tmp_path


def _evidence(tmp_path: Path) -> Path:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(EVIDENCE))
    return path


def _land(
    project: Project, repo: Path, tmp_path: Path, *, runner: str | None = None
) -> task_close.Closure:
    landed = land_task.land(project, repo, "a", _evidence(tmp_path))
    if runner is not None:
        check = landed.checks[0]
        stored = project.get(check.check_run_id, "tuner:check-run")
        forged = project.create(
            record_type="tuner:check-run",
            subject="a",
            payload={**stored["payload"], "runner": runner},
        )
        landed = replace(landed, checks=(replace(check, check_run_id=forged["id"]),))
    return task_close.close(project, landed, frozenset({"R1"}))


def _state(project: Project) -> str:
    return project.resolve("score:work-item", "a")["lifecycle_state"]


def _land_cli(repo: Path, evidence: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "orchestra.cli",
            "task",
            "land",
            "a",
            "--evidence",
            str(evidence),
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )


def test_r16_closes_the_task_through_the_cli_when_the_decision_approves(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    result = _land_cli(repo, _evidence(tmp_path))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["state"] == "done"
    assert _state(project) == "done"


def test_r16_asks_the_close_decision_with_the_project_and_the_landed_criteria(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo = _world(tmp_path)
    calls: list[tuple[Project, list[CriterionRequest], list[str]]] = []

    def approve(
        asked: Project,
        criteria: list[CriterionRequest],
        *,
        acceptance_ids: list[str],
        cwd: Path,
        transition: str = "done",
        has_finding: bool = False,
    ) -> CloseApproval:
        calls.append((asked, criteria, acceptance_ids))
        return CloseApproval()

    monkeypatch.setattr(task_close, "decide_close", approve)
    closure = _land(project, repo, tmp_path)
    assert closure.state == "done"
    assert len(calls) == 1
    asked, criteria, acceptance_ids = calls[0]
    assert asked is project
    assert [c["criterion_id"] for c in criteria] == acceptance_ids
    assert [c["method"] for c in criteria] == ["check"]
    assert criteria[0]["check_run_id"]


def test_r16_leaves_no_second_copy_of_the_gates_in_task_close() -> None:
    assert not hasattr(task_close, "_policy_problem")
    assert not hasattr(task_close, "_red_check_run")


def test_r17_reports_a_refusal_of_the_close_decision_and_keeps_the_task_in_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo = _world(tmp_path)

    def refuse(*_args: object, **_kwargs: object) -> CloseRefusal:
        return CloseRefusal("the decision says no")

    monkeypatch.setattr(task_close, "decide_close", refuse)
    closure = _land(project, repo, tmp_path)
    assert closure.state == "in_progress"
    assert closure.reasons == ("the decision says no",)
    assert _state(project) == "in_progress"


def test_r17_refuses_a_check_run_the_runner_did_not_produce(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    closure = _land(project, repo, tmp_path, runner="hand")
    assert closure.state == "in_progress"
    assert len(closure.reasons) == 1
    assert closure.reasons[0].endswith(
        "check-run is not runner-produced (runner must be 'orchestra', got 'hand')"
    )
    assert _state(project) == "in_progress"


def test_r17_refuses_a_tdd_task_with_no_red_check_run(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"method": "tdd"})
    closure = _land(project, repo, tmp_path)
    assert closure.state == "in_progress"
    assert len(closure.reasons) == 1
    assert closure.reasons[0].endswith(
        "tdd done close requires red_check_run_id (runner-produced fail preceding the green)"
    )
    assert _state(project) == "in_progress"


def test_r17_refuses_an_incomplete_oracle_freeze(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"oracle_hashes": ["tests/t.py:sha256:" + "a" * 64]})
    closure = _land(project, repo, tmp_path)
    assert closure.state == "in_progress"
    assert len(closure.reasons) == 1
    assert "incomplete oracle freeze or invalid policy" in closure.reasons[0]
    assert _state(project) == "in_progress"


def test_r17_refuses_a_claim_when_the_manifest_is_missing(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"claim": "claim-widget"})
    closure = _land(project, repo, tmp_path)
    assert closure.state == "in_progress"
    assert closure.reasons == ("claim manifest is missing",)
    assert _state(project) == "in_progress"


def test_r17_refuses_a_claim_the_manifest_does_not_list(tmp_path: Path) -> None:
    project, repo = _world(tmp_path, {"claim": "claim-widget"})
    tree = Path(str(project.resolve("score:work-item", "a")["payload"].get("write_root") or repo))
    (tree / ".tuner").mkdir()
    (tree / ".tuner" / "manifest.json").write_text(json.dumps({"claims": [{"id": "other"}]}))
    closure = _land(project, repo, tmp_path)
    assert closure.state == "in_progress"
    assert len(closure.reasons) == 1
    assert closure.reasons[0].endswith("claim 'claim-widget' is not listed in .tuner/manifest.json")
    assert _state(project) == "in_progress"
