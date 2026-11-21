"""Temporary worlds and in-process entry-point calls for the interface pins."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from canon_support import create, make_project, seed_effort

from orchestra.canon.cli import main as canon_main
from orchestra.cli import main as orchestra_main


def _load_root_conftest() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "conftest.py"
    spec = importlib.util.spec_from_file_location("root_conftest", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_ROOT = _load_root_conftest()
build_store: Callable[..., Path] = _ROOT.build_store
run_cli: Callable[..., subprocess.CompletedProcess[str]] = _ROOT.run_cli

EFFORT = "alpha"
PHASE = "p1"
TASK = "a"
PHASE_BODY = (
    "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n"
    "## Landing\n\nbranch: phase/p1\nbase: main\n"
)
SPEC_BODY = (
    "## Requirements\n\nR1: It works.\n\n## Acceptance criteria\n\nx\n\n"
    "## Constraints\n\nx\n\n## Non-goals\n\nx\n\n## Invariants\n\nx\n\n## Assumptions\n\nx"
)

EntryPoint = Callable[[list[str] | None], int]
ENTRY_POINTS: dict[str, EntryPoint] = {"orchestra": orchestra_main, "canon": canon_main}


@dataclass(frozen=True)
class Result:
    code: int
    out: str
    err: str


def invoke(tool: str, argv: list[str], cwd: Path, stdin: str = "") -> Result:
    entry = ENTRY_POINTS[tool]
    out, err = io.StringIO(), io.StringIO()
    previous = Path.cwd()
    previous_stdin = sys.stdin
    os.chdir(cwd)
    sys.stdin = io.StringIO(stdin)
    code: int
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = entry(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.stdin = previous_stdin
        os.chdir(previous)
    return Result(code, out.getvalue(), err.getvalue())


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def build_world(root: Path, *, wave_started: bool = False) -> Path:
    project = make_project(root)
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    (root / "base.txt").write_text("base\n")
    _git(root, "add", "base.txt")
    _git(root, "commit", "-qm", "base")
    _git(root, "branch", "-M", "main")
    seed_effort(project, EFFORT, PHASE)
    phase = project.resolve("score:phase", PHASE)
    assert "body" in phase
    project.update(phase["id"], body=PHASE_BODY)
    create(
        project,
        "score:specification",
        PHASE,
        {"weight": "full", "phase": PHASE, "effort": EFFORT, "requirements": ["R1"]},
        SPEC_BODY,
    )
    create(
        project,
        "score:work-item",
        TASK,
        {
            "title": "Task a",
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
        TASK,
        {
            "method": "check",
            "phase": PHASE,
            "effort": EFFORT,
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    _git(root, "branch", f"phase/{PHASE}", "main")
    (root / ".worktrees").mkdir()
    _git(root, "worktree", "add", "-q", str(root / ".worktrees" / PHASE), f"phase/{PHASE}")
    if wave_started:
        started = invoke("orchestra", ["wave", "start", PHASE], root)
        assert started.code == 0, started.err
    return root


def seed_view_records(root: Path) -> None:
    def create_record(
        record_type: str, subject: str, payload: dict[str, object], body: str
    ) -> None:
        argv = [
            "create",
            "--type",
            record_type,
            "--subject",
            subject,
            "--payload",
            json.dumps(payload),
            "--body",
            body,
        ]
        created = invoke("canon", argv, root)
        assert created.code == 0, created.out

    create_record(
        "score:work-item",
        "b",
        {
            "title": "Task b",
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "",
            "effort": EFFORT,
            "executor": "inline",
            "depends_on": [TASK],
            "requirements": ["R1"],
        },
        "## Description\n\nR1: Second step.\n\n## Approach\n\nDo it later.",
    )
    create_record(
        "score:continuity-question",
        "which-store",
        {"owner": "human", "blocking": True, "scope": EFFORT},
        "## Question\n\nWhich store?\n\n## Options\n\n- one\n- two",
    )
    create_record("composer:area", "dashboard", {"title": "Dashboard"}, "## Scope\n\nThe web UI.")
    create_record("composer:idea", "dark-mode", {"status": "open", "area": "dashboard"}, "")
    create_record("composer:idea", "loose-end", {"status": "open"}, "")
    create_record(
        "composer:idea",
        "shipped-thing",
        {"status": "promoted", "area": "dashboard", "effort": EFFORT},
        "",
    )
    create_record("composer:placement", EFFORT, {"area": "dashboard"}, "")
