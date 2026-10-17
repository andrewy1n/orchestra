"""execute-phase requires a commit per task on the phase branch before verify."""

from __future__ import annotations

import re

from conftest import REPO_ROOT

SKILL = REPO_ROOT / "skills" / "execute-phase" / "SKILL.md"


def _text() -> str:
    return re.sub(r"\s+", " ", SKILL.read_text())


def test_execute_phase_requires_a_commit_per_task_before_verify():
    text = _text()
    assert "after each task's code lands and before verify" in text
    assert "commit per task" in text
    assert "passing check-run can carry a real SHA" in text


def test_task_commit_excludes_artifacts_on_the_phase_branch():
    text = _text()
    assert "commits on the phase branch from the worktree" in text
    assert "That commit excludes `.artifacts`" in text
    assert "add -A -- . ':!.artifacts'" in text
