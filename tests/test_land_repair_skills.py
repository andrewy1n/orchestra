"""The land step repairs a failing CI check without a user step, inside the retry budgets."""

from __future__ import annotations

import re

from conftest import REPO_ROOT

PHASE_END = REPO_ROOT / "shared/phase-end.md"


def _repair_loop() -> str:
    text = PHASE_END.read_text(encoding="utf-8")
    start = text.find("\n### CI repair loop\n")
    if start == -1:
        return ""
    following = re.search(r"\n#{1,3} (?!CI repair loop\n)", text[start + 1 :])
    end = start + 1 + following.start() if following else len(text)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def test_ci_failure_creates_repair_work_item() -> None:
    section = _repair_loop()

    assert "`orchestra land` exits 1 with a failed check" in section
    assert "Create a repair work-item" in section
    assert "each failing check passes" in section


def test_repair_runs_through_wave_in_phase_worktree() -> None:
    assert "execute wave in the phase worktree" in _repair_loop()


def test_repair_uses_task_executor_rules() -> None:
    assert "executor rules of a task" in _repair_loop()


def test_repair_commit_after_acceptance() -> None:
    section = _repair_loop()

    assert "After the repair passes its acceptance, commit the repair" in section
    assert "commit the repair in the phase worktree" in section


def test_repair_pushes_via_land_rerun() -> None:
    section = _repair_loop()

    assert "Run `orchestra land --phase <phase-slug>` again" in section
    assert "Land pushes the commit" in section


def test_land_rereads_ci() -> None:
    assert "reads CI again" in _repair_loop()


def test_repairs_follow_retry_budgets() -> None:
    section = _repair_loop()

    assert "retry budgets" in section
    assert "`retry_max_fix_tasks`" in section
    assert "`retry_max_redispatches`" in section


def test_exhausted_budget_opens_needs_you_finding() -> None:
    section = _repair_loop()

    assert "When a retry budget runs out" in section
    assert "`score:continuity-question`" in section
    assert "`tuner:finding`" in section
    assert "retry:<repair-task-slug>" in section


def test_exhausted_budget_stops_dispatch() -> None:
    section = _repair_loop()

    assert "Do not create another repair" in section
    assert "Stop until the user answers" in section


def test_a_moved_head_redoes_the_gate_terms_before_land() -> None:
    section = _repair_loop()

    assert "`orchestra gate`" in section
    assert "new proof packet" in section
