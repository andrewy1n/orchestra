"""execute-phase states per-task worktrees when Landing is present."""

from __future__ import annotations

import re
from pathlib import Path

from conftest import REPO_ROOT

SKILL = REPO_ROOT / "skills" / "execute-phase" / "SKILL.md"
PHASE_END = REPO_ROOT / "skills" / "execute-phase" / "references" / "phase-end.md"

_VERIFICATION = "the work-item that depends_on every other phase work-item"
_OTHER = f"a task other than {_VERIFICATION}"


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text())


def test_r1_landing_creates_a_task_branch_except_the_verification_task():
    text = _flat(SKILL)
    assert (
        "When Landing is present, at the start of a wave, execute-phase creates branch "
        "`task/<phase-slug>/<task-slug>` from the current `phase/<phase-slug>` tip for every "
        f"task in that wave except {_VERIFICATION}."
        in text
    )


def test_r2_landing_adds_a_task_worktree_except_the_verification_task():
    text = _flat(SKILL)
    assert (
        "When Landing is present, at the start of a wave, execute-phase adds worktree "
        "`<repo>/.worktrees/<phase-slug>--<task-slug>` checked out on that task branch for every "
        f"task in that wave except {_VERIFICATION}."
        in text
    )


def test_r3_per_task_commit_runs_in_that_task_worktree():
    text = _flat(SKILL)
    assert f"The per-task commit for {_OTHER} runs in that task worktree." in text


def test_r4_per_task_commit_stages_with_git_add_excluding_artifacts():
    text = _flat(SKILL)
    assert "That per-task commit stages with `git add -A` excluding `.artifacts`." in text


def test_r5_verify_work_runs_in_that_task_worktree():
    text = _flat(SKILL)
    assert f"verify-work for {_OTHER} runs in that task worktree." in text


def test_r6_passing_check_run_records_that_task_commit():
    text = _flat(SKILL)
    assert (
        f"A passing check-run for {_OTHER} records that task's commit as its revision."
        in text
    )


def test_r7_wave_end_merges_passing_task_branches_into_the_phase_branch():
    text = _flat(SKILL)
    assert (
        "At wave end, the parent merges each passing task branch of "
        f"{_OTHER} into `phase/<phase-slug>`."
        in text
    )


def test_r8_wave_end_merges_run_in_task_slug_order():
    text = _flat(SKILL)
    assert "Those wave-end merges run in task-slug order." in text


def test_r9_wave_end_integration_does_not_rebase_the_task_branch():
    text = _flat(SKILL)
    assert "The wave-end integration does not rebase the task branch." in text


def test_r10_parent_does_not_merge_a_task_branch_whose_check_did_not_pass():
    text = _flat(SKILL)
    assert "The parent does not merge a task branch whose check did not pass." in text


def test_r11_conflict_leaves_that_conflict_unresolved():
    text = _flat(SKILL)
    assert (
        "When a merge between a task branch and the phase branch conflicts, "
        "the parent leaves that conflict unresolved."
        in text
    )


def test_r12_conflict_opens_a_blocking_continuity_question_on_the_effort():
    text = _flat(SKILL)
    assert (
        "When a merge between a task branch and the phase branch conflicts, "
        "the parent opens a blocking continuity question on the effort."
        in text
    )


def test_r13_conflict_does_not_start_the_next_wave():
    text = _flat(SKILL)
    assert (
        "When a merge between a task branch and the phase branch conflicts, "
        "the parent does not start the next wave."
        in text
    )


def test_r14_redispatch_reuses_the_task_branch():
    text = _flat(SKILL)
    assert (
        f"Re-dispatch of {_OTHER} reuses branch `task/<phase-slug>/<task-slug>`."
        in text
    )


def test_r15_redispatch_reuses_the_task_worktree():
    text = _flat(SKILL)
    assert (
        "Re-dispatch of "
        f"{_OTHER} reuses worktree `<repo>/.worktrees/<phase-slug>--<task-slug>`."
        in text
    )


def test_r16_redispatch_merges_the_phase_tip_into_the_task_branch():
    text = _flat(SKILL)
    assert (
        "Before a re-dispatch continues, the parent merges `phase/<phase-slug>` into the "
        "task branch when the task branch does not already contain the phase tip."
        in text
    )


def test_r17_verification_task_is_dispatched_in_the_phase_worktree():
    text = _flat(SKILL)
    assert (
        "The work-item that depends_on every other phase work-item is dispatched in "
        "`<repo>/.worktrees/<phase-slug>` on `phase/<phase-slug>`."
        in text
    )


def test_r18_no_task_branch_for_the_verification_task():
    text = _flat(SKILL)
    assert f"execute-phase does not create a task branch for {_VERIFICATION}." in text


def test_r19_no_task_worktree_for_the_verification_task():
    text = _flat(SKILL)
    assert f"execute-phase does not add a task worktree for {_VERIFICATION}." in text


def test_r20_absent_landing_does_not_create_a_task_branch():
    text = _flat(SKILL)
    assert (
        "When Landing is absent, execute-phase does not create a "
        "`task/<phase-slug>/<task-slug>` branch."
        in text
    )


def test_r21_absent_landing_does_not_add_a_task_worktree():
    text = _flat(SKILL)
    assert (
        "When Landing is absent, execute-phase does not add a "
        "`<repo>/.worktrees/<phase-slug>--<task-slug>` worktree."
        in text
    )


def test_r22_phase_close_removes_each_task_worktree():
    text = _flat(PHASE_END)
    assert (
        "At phase close, the parent removes each task worktree "
        "`<repo>/.worktrees/<phase-slug>--<task-slug>` for that phase."
        in text
    )


def test_r23_phase_close_deletes_task_branches_contained_in_the_phase_branch():
    text = _flat(PHASE_END)
    assert (
        "At phase close, the parent deletes each `task/<phase-slug>/<task-slug>` "
        "branch that is contained in the phase branch."
        in text
    )


def test_r24_orientation_names_the_task_worktree_as_the_write_root():
    text = _flat(SKILL)
    assert (
        "The assignment orientation names that task worktree as the executor's write root."
        in text
    )


def test_r25_orientation_does_not_tell_the_executor_to_avoid_git_add():
    text = _flat(SKILL)
    assert (
        "The assignment orientation does not tell the executor to avoid `git add -A`."
        in text
    )


def test_r26_no_empty_commit_when_a_task_has_nothing_to_commit():
    text = _flat(SKILL)
    assert (
        f"When {_OTHER} has nothing to commit, execute-phase does not create an empty commit."
        in text
    )
