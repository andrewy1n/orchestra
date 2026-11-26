from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from canon_support import REPO, create, make_project

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from dashboard.backend.server.app import create_app
from orchestra.canon.project import Project, open_store
from orchestra.canon.types import Record
from orchestra.conductor.phases.workflow.workflow_review import record_step_review

PHASE = "right-size"
EFFORT = "right-size-effort"
LANDING = (
    "## Problem\n\nA test phase.\n\n## Approach\n\nTest dispatch.\n\n"
    "## Exit criteria\n\nWave dispatch passes.\n\n"
    "## Landing\n\nbranch: phase/right-size\nbase: main\n"
)
SPEC_BODY = (
    "## Requirements\nR1: Show medians.\n"
    "## Acceptance criteria\nR1 passes.\n"
    "## Constraints\nKeep scope fixed.\n"
    "## Non-goals\nNo unrelated changes.\n"
    "## Invariants\nApproval remains explicit.\n"
    "## Assumptions\nThe store is available.\n"
)
DESIGN_BODY = (
    "## Architecture\nUse workflow records.\n"
    "## Interfaces\nUse typed APIs.\n"
    "## Decisions\nPersist reviews.\n"
    "## Invariants\nDo not infer approval.\n"
    "## Assumptions\nThe phase exists.\n"
    "## Tradeoffs\nKeep writes atomic.\n"
    "## Risks\nStale inputs need review.\n"
)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


def _env() -> dict[str, str]:
    return dict(os.environ, PYTHONPATH=str(REPO))


def _orchestra(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *args],
        capture_output=True,
        text=True,
        cwd=repo,
        env=_env(),
    )


def _repo(tmp_path: Path, *, lone: int | None = None) -> tuple[Project, Path]:
    project = make_project(tmp_path)
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "test")
    (tmp_path / "base.txt").write_text("base\n", encoding="utf-8")
    setting = "" if lone is None else f"lone_task_inline_minutes = {lone}\n"
    (tmp_path / "orchestra.toml").write_text(
        '[verify.stages]\ntask = ["unit"]\nphase = ["unit", "review"]\n\n'
        '[verify.unit]\nrunner = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]\n'
        f"\n[execute]\nsmall_wave_budget_minutes = 15\n{setting}",
        encoding="utf-8",
    )
    _git(tmp_path, "add", "base.txt", "orchestra.toml")
    _git(tmp_path, "commit", "-qm", "base")
    _git(tmp_path, "branch", "-M", "main")
    create(project, "score:effort", EFFORT, {"goal": "test", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Right size", "ordinal": 1, "effort": EFFORT},
        LANDING,
    )
    _git(tmp_path, "branch", f"phase/{PHASE}", "main")
    (tmp_path / ".worktrees").mkdir(exist_ok=True)
    _git(tmp_path, "worktree", "add", "-q", str(tmp_path / ".worktrees" / PHASE), f"phase/{PHASE}")
    return project, tmp_path


def _item(
    project: Project, slug: str, *, size: str | None = None, estimate_minutes: int | None = None
) -> None:
    payload: dict[str, object] = {
        "title": slug,
        "phase": PHASE,
        "kind": "deliver",
        "assignee": "",
        "effort": EFFORT,
    }
    if size is not None:
        payload["size"] = size
    if estimate_minutes is not None:
        payload["estimate_minutes"] = estimate_minutes
    create(project, "score:work-item", slug, payload, f"## Description\n\nDo {slug}.")


def _start(repo: Path) -> list[dict[str, object]]:
    result = _orchestra(repo, "wave", "start", PHASE, "--json")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["tasks"]


@pytest.mark.parametrize(("estimate", "expected"), [(10, "inline"), (11, "subagent")])
def test_wave_start_picks_lone_task_executor_from_estimate(
    tmp_path: Path, estimate: int, expected: str
) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "lone", size="M", estimate_minutes=estimate)

    assert {task["executor"] for task in _start(repo)} == {expected}


def test_wave_start_keeps_written_executor_on_lone_task(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    create(
        project,
        "score:work-item",
        "lone",
        {
            "title": "lone",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "size": "XS",
            "estimate_minutes": 4,
            "executor": "subagent",
        },
        "## Description\n\nDo lone.",
    )

    assert {task["executor"] for task in _start(repo)} == {"subagent"}


def test_setting_moves_the_lone_task_threshold(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path, lone=5)
    _item(project, "lone", size="M", estimate_minutes=8)

    assert {task["executor"] for task in _start(repo)} == {"subagent"}


def _view_executor(repo: Path, task: str) -> str:
    result = _orchestra(repo, "view", "plan", "--effort", EFFORT)
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if task in line]
    assert lines, result.stdout
    return "inline" if "inline" in lines[0] else "subagent"


def test_view_plan_and_dashboard_agree_on_the_lone_task_executor(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "lone", size="M", estimate_minutes=8)
    record = next(item for item in project.records() if item["record_type"] == "score:work-item")

    client = TestClient(create_app(open_store(repo)))
    body = client.get("/api/task", params={"id": record["id"]}).json()

    assert _view_executor(repo, "lone") == "inline"
    assert body["detail"]["executor"] == "inline"


def _approve_spec(project: Project, artifact: Record) -> None:
    record_step_review(
        project,
        phase=PHASE,
        step="spec",
        artifact=artifact,
        authority="user-approval",
        basis="Approved.",
        source_reviews=[],
    )


def _approve_design(project: Project, artifact: Record) -> None:
    record_step_review(
        project,
        phase=PHASE,
        step="design",
        artifact=artifact,
        authority="user-approval",
        basis="Approved.",
        source_reviews=[],
    )


def _report(project: Project, slug: str, duration_s: float) -> None:
    project.create(
        record_type="conductor:execution-report",
        subject=f"{slug}-report",
        payload={
            "work_item": slug,
            "result": "done",
            "verdict": "pass",
            "revision": "abc123",
            "duration_s": duration_s,
        },
        body="Report.",
    )


def test_brief_shows_bands_medians_and_no_data(tmp_path: Path) -> None:
    project, repo = _repo(tmp_path)
    specification = project.create(
        record_type="score:specification",
        subject="right-size-spec",
        payload={"weight": "full", "phase": PHASE, "effort": EFFORT, "requirements": ["R1"]},
        body=SPEC_BODY,
    )
    _approve_spec(project, specification)
    design = project.create(
        record_type="score:design",
        subject="right-size-design",
        payload={"phase": PHASE, "effort": EFFORT, "decisions": []},
        body=DESIGN_BODY,
    )
    _approve_design(project, design)
    _item(project, "small-a", size="S")
    _item(project, "small-b", size="S")
    _report(project, "small-a", 120)
    _report(project, "small-b", 360)

    result = _orchestra(repo, "workflow", "brief", PHASE, "tasks")

    assert result.returncode == 0, result.stderr
    assert "XS 1–2, S 2–5, M 5–10, L 10–20, XL 20–40" in result.stdout
    assert "- S: 4.0 min median, 2 samples" in result.stdout
    assert "- XL: no data" in result.stdout
