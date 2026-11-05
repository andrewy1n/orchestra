from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from canon_support import REPO, create, make_project

from orchestra.canon.project import Project
from orchestra.conductor import land_task, wave
from orchestra.conductor.evidence import EvidenceError, parse_evidence

PHASE = "ph"
EFFORT = "ef"
PHASE_BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n"
    "## Landing\n\nbranch: phase/ph\nworktree: <repo>/.worktrees/ph\nbase: main\n"
)
EVIDENCE = {
    "subject": "a",
    "kind": "deliver",
    "result": "pass",
    "verdict": "pass",
    "evidence": "ran the acceptance",
}


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _world(tmp_path: Path, verify_command: str = "true") -> tuple[Project, Path, Path]:
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
    spec = {"weight": "full", "phase": PHASE, "effort": EFFORT, "requirements": ["R1"]}
    create(
        project,
        "score:specification",
        PHASE,
        spec,
        "## Requirements\n\nR1: It works.\n\n## Acceptance criteria\n\nx\n\n## Constraints\n\nx\n\n## Non-goals\n\nx\n\n## Invariants\n\nx\n\n## Assumptions\n\nx",
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
    create(
        project,
        "score:acceptance",
        "a",
        {
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": verify_command,
            "requirement": "R1",
        },
    )
    wave.start(project, tmp_path, PHASE)
    tree = tmp_path / ".worktrees" / "ph--a"
    return project, tmp_path, tree


def _evidence_file(tmp_path: Path, **override: object) -> Path:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({**EVIDENCE, **override}))
    return path


def _land_cli(repo: Path, evidence: Path, *extra: str) -> subprocess.CompletedProcess[str]:
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
            *extra,
        ],
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )


def test_r07_rejects_evidence_with_a_missing_required_field(tmp_path: Path) -> None:
    path = _evidence_file(tmp_path)
    data = json.loads(path.read_text())
    del data["verdict"]
    path.write_text(json.dumps(data))
    with pytest.raises(EvidenceError, match="verdict"):
        parse_evidence(path)


def test_r07_rejects_evidence_with_an_unknown_field_and_writes_nothing(tmp_path: Path) -> None:
    project, repo, _ = _world(tmp_path)
    path = _evidence_file(tmp_path, surprise="x")
    result = _land_cli(repo, path)
    assert result.returncode != 0
    assert "surprise" in result.stderr
    assert project.list("conductor:execution-report") == []


def test_r08_commits_the_task_worktree_without_canon(tmp_path: Path) -> None:
    project, repo, tree = _world(tmp_path)
    (tree / "work.txt").write_text("work\n")
    (tree / ".canon").mkdir(exist_ok=True)
    (tree / ".canon" / "x.txt").write_text("meta\n")
    landed = land_task.land(project, repo, "a", _evidence_file(tmp_path))
    assert landed.commit == _git(tree, "rev-parse", "HEAD")
    assert _git(tree, "show", "--name-only", "--format=", "HEAD") == "work.txt"


def test_r08_creates_no_empty_commit_for_a_clean_worktree(tmp_path: Path) -> None:
    project, repo, tree = _world(tmp_path)
    before = _git(tree, "rev-parse", "HEAD")
    landed = land_task.land(project, repo, "a", _evidence_file(tmp_path))
    assert landed.commit == ""
    assert _git(tree, "rev-parse", "HEAD") == before


def test_r09_writes_the_execution_report_with_evidence_and_revision(tmp_path: Path) -> None:
    project, repo, tree = _world(tmp_path)
    (tree / "work.txt").write_text("work\n")
    landed = land_task.land(project, repo, "a", _evidence_file(tmp_path))
    report = project.get(landed.report_id, "conductor:execution-report")
    assert report["payload"]["revision"] == _git(tree, "rev-parse", "HEAD")
    assert "evidence: ran the acceptance" in report.get("body", "")


def test_r10_runs_every_active_acceptance_at_the_landed_revision(tmp_path: Path) -> None:
    project, repo, tree = _world(tmp_path)
    create(
        project,
        "score:acceptance",
        "a-extra",
        {
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    (tree / "work.txt").write_text("work\n")
    landed = land_task.land(project, repo, "a", _evidence_file(tmp_path))
    assert [c.subject for c in landed.checks] == ["a", "a-extra"]
    runs = project.list("tuner:check-run")
    assert [r["payload"]["revision"] for r in runs] == [landed.revision] * len(runs)


def test_r11_closes_the_task_when_its_requirements_are_verified(tmp_path: Path) -> None:
    project, repo, _ = _world(tmp_path)
    result = _land_cli(repo, _evidence_file(tmp_path))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["state"] == "done"
    assert project.resolve("score:work-item", "a")["lifecycle_state"] == "done"


def test_r11_leaves_the_task_in_progress_when_a_check_fails(tmp_path: Path) -> None:
    project, repo, _ = _world(tmp_path, verify_command="false")
    result = _land_cli(repo, _evidence_file(tmp_path))
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)["state"] == "in_progress"
    assert project.resolve("score:work-item", "a")["lifecycle_state"] == "in_progress"
