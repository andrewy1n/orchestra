"""Skills integrate the phase branch with `orchestra land`, not by hand."""

from __future__ import annotations

import re

from conftest import REPO_ROOT

SKILLS = REPO_ROOT / "skills"
HAND_INTEGRATION = (
    "as the repo's own contributor instructions describe",
    "contributor instructions do not say how a finished branch lands",
    "gh pr merge",
)


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _assert_lands(text: str) -> None:
    flat = _flat(text)
    assert "orchestra land <phase-slug>" in flat
    assert "runs `orchestra gate` first" in flat
    assert "`merge: <command>`" in flat
    assert "`suite: <command>`" in flat
    assert "Exit 2 means the Landing section names no `merge:` line" in flat
    for phrase in HAND_INTEGRATION:
        assert phrase not in flat


def test_execute_phase_calls_orchestra_land() -> None:
    _assert_lands((SKILLS / "execute-phase" / "SKILL.md").read_text())


def test_phase_end_calls_orchestra_land() -> None:
    _assert_lands((SKILLS / "execute-phase" / "references" / "phase-end.md").read_text())


def test_plan_phase_landing_allows_merge_and_suite_lines() -> None:
    flat = _flat((SKILLS / "plan-phase" / "SKILL.md").read_text())
    assert "Landing may carry a `merge: <command>` line" in flat
    assert "an optional `suite: <command>` line" in flat
    assert "Do not write it as a prose step" in flat
    for phrase in HAND_INTEGRATION:
        assert phrase not in flat


def test_execute_phase_keeps_wave_end_task_branch_merges() -> None:
    flat = _flat((SKILLS / "execute-phase" / "SKILL.md").read_text())
    assert "merge task/<phase-slug>/<task-slug>" in flat
