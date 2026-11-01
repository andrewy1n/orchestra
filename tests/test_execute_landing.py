"""execute-phase lands the phase branch when the phase body has a Landing section."""

from __future__ import annotations

import re

from conftest import REPO_ROOT
from test_phase_landing import MERGE_STEP, PUSH_STEP, STORE_COMMIT_STEP, affirmative_matches

SKILLS = REPO_ROOT / "skills"


def _raw(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text()


def _text(name: str) -> str:
    return re.sub(r"\s+", " ", _raw(name))


def test_landing_worktree_confines_code_and_keeps_the_store_on_the_primary_checkout():
    text = _text("execute-phase")
    assert "<repo>/.worktrees/<phase-slug>" in text
    assert "code writes only under the worktree" in text
    assert "store writes on the primary checkout" in text


def test_phase_close_commits_the_phase_branch_without_a_default_branch_merge():
    text = _text("execute-phase")
    assert "commit the phase branch" in text
    raw = _raw("execute-phase")
    assert affirmative_matches(raw, MERGE_STEP) == []
    assert affirmative_matches(raw, STORE_COMMIT_STEP) == []
    phase_end = (SKILLS / "execute-phase" / "references" / "phase-end.md").read_text()
    assert "git -C <primary-checkout> merge phase/<phase-slug>" not in phase_end


def test_phase_close_omits_push_step():
    assert affirmative_matches(_raw("execute-phase"), PUSH_STEP) == []


def test_missing_landing_section_stays_in_the_current_checkout():
    text = _text("execute-phase")
    assert "a missing Landing section stays in the current checkout" in text
