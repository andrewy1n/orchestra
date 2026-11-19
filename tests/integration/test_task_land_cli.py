from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from canon_support import REPO, create, make_project

from orchestra import cli
from orchestra.conductor import wave
from orchestra.conductor.evidence import EVIDENCE_SCHEMA

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
JSON_FIELDS = [
    "task",
    "commit",
    "revision",
    "execution_report",
    "check_runs",
    "state",
    "reasons",
    "question",
]


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _world(tmp_path: Path, verify_command: str) -> Path:
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
    return tmp_path


def _evidence(root: Path) -> Path:
    path = root / "evidence.json"
    path.write_text(json.dumps(EVIDENCE))
    return path


def _orchestra(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(REPO))
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def _normalised(text: str) -> str:
    text = re.sub(r"rec-[0-9a-f-]{36}", "<id>", text)
    return re.sub(r"\b[0-9a-f]{40}\b", "<sha>", text)


def test_r5_passing_landing_prints_the_json_fields(tmp_path: Path) -> None:
    repo = _world(tmp_path, "true")
    result = _orchestra(repo, "task", "land", "a", "--evidence", str(_evidence(tmp_path)), "--json")
    assert result.returncode == 0, result.stderr
    assert list(json.loads(result.stdout)) == JSON_FIELDS
    assert json.loads(_normalised(result.stdout)) == {
        "task": "a",
        "commit": "",
        "revision": "<sha>",
        "execution_report": "<id>",
        "check_runs": ["<id>"],
        "state": "done",
        "reasons": [],
        "question": "",
    }


def test_r5_refused_landing_prints_the_json_fields(tmp_path: Path) -> None:
    repo = _world(tmp_path, "false")
    result = _orchestra(repo, "task", "land", "a", "--evidence", str(_evidence(tmp_path)), "--json")
    assert result.returncode == 1, result.stderr
    assert list(json.loads(result.stdout)) == JSON_FIELDS
    assert json.loads(_normalised(result.stdout)) == {
        "task": "a",
        "commit": "",
        "revision": "<sha>",
        "execution_report": "<id>",
        "check_runs": ["<id>"],
        "state": "in_progress",
        "reasons": ["a: check-run <id> result=fail revision=<sha>"],
        "question": "",
    }


def test_r6_passing_landing_prints_the_text_line(tmp_path: Path) -> None:
    repo = _world(tmp_path, "true")
    result = _orchestra(repo, "task", "land", "a", "--evidence", str(_evidence(tmp_path)))
    assert result.returncode == 0, result.stderr
    assert _normalised(result.stdout) == "a: done (report <id>, revision <sha>)\n"
    assert result.stderr == ""


def test_r6_refused_landing_prints_the_text_line_and_reasons(tmp_path: Path) -> None:
    repo = _world(tmp_path, "false")
    result = _orchestra(repo, "task", "land", "a", "--evidence", str(_evidence(tmp_path)))
    assert result.returncode == 1
    assert _normalised(result.stdout) == "a: in_progress (report <id>, revision <sha>)\n"
    assert _normalised(result.stderr) == "  a: check-run <id> result=fail revision=<sha>\n"


def test_r7_unknown_work_item_exits_2_naming_the_task(tmp_path: Path) -> None:
    repo = _world(tmp_path, "true")
    result = _orchestra(repo, "task", "land", "nope", "--evidence", str(_evidence(tmp_path)))
    assert result.returncode == 2
    assert result.stderr.startswith("orchestra task land: nope: ")
    assert result.stdout == ""


def test_r7_unreadable_evidence_exits_2_naming_the_task(tmp_path: Path) -> None:
    repo = _world(tmp_path, "true")
    result = _orchestra(repo, "task", "land", "a", "--evidence", str(tmp_path / "missing.json"))
    assert result.returncode == 2
    assert result.stderr.startswith("orchestra task land: a: ")
    assert result.stdout == ""


def test_r7_unreadable_store_exits_2_naming_the_task(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = _orchestra(empty, "task", "land", "a", "--evidence", str(_evidence(tmp_path)))
    assert result.returncode == 2
    assert result.stderr.startswith("orchestra task land: a: ")
    assert result.stdout == ""


def test_r8_schema_prints_the_evidence_schema_and_exits_0(tmp_path: Path) -> None:
    result = _orchestra(tmp_path, "task", "land", "--schema")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == json.loads(json.dumps(EVIDENCE_SCHEMA))
    assert result.stderr == ""


def test_r13_handler_calls_land_and_close_and_computes_no_requirement_status() -> None:
    source = inspect.getsource(cli._cmd_task_land)
    assert "land_and_close" in source
    assert "requirement_status" not in source
    assert "task_close" not in source
    assert hasattr(cli, "land_and_close")
