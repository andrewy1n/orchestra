"""Skills integrate the phase branch with `orchestra land`, not by hand."""

from __future__ import annotations

import re

from conftest import REPO_ROOT
from helpers import skill_text

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
    assert "orchestra land --phase <phase-slug>" in flat
    assert "runs `orchestra gate` first" in flat
    assert "`merge: <command>`" not in flat
    assert "`suite: <command>`" not in flat
    for phrase in HAND_INTEGRATION:
        assert phrase not in flat


def test_execute_phase_calls_orchestra_land() -> None:
    _assert_lands(skill_text("execute"))


def test_phase_end_calls_orchestra_land() -> None:
    _assert_lands((SKILLS / "verify" / "references" / "phase-end.md").read_text())


def test_landing_section_has_no_merge_or_suite_command() -> None:
    texts = [
        skill_text("tasks"),
        skill_text("execute"),
        (SKILLS / "verify" / "references" / "phase-end.md").read_text(),
        (REPO_ROOT / "shared" / "kinds-and-focus.md").read_text(),
        (REPO_ROOT / "README.md").read_text(),
    ]
    for text in texts:
        flat = _flat(text)
        assert "`merge: <command>`" not in flat
        assert "`suite: <command>`" not in flat
        assert "replaces `phase_gate.suite.command`" not in flat
        assert "suite policy --phase" not in flat
        for phrase in HAND_INTEGRATION:
            assert phrase not in flat
    plan = _flat(texts[0])
    assert "Landing names branch, worktree, base and repo only" in plan
    assert "`[land]` and `[suite]` configure them" in plan
    shared = _flat(texts[3])
    assert "names branch, worktree, base and repo only" in shared
    assert "`orchestra.toml` `[land]` and `[suite]` configure the adapter" in shared


def test_execute_phase_keeps_wave_end_task_branch_merges() -> None:
    flat = _flat(skill_text("execute"))
    assert "merge task/<phase-slug>/<task-slug>" in flat


def test_phase_gate_terms_name_needs_human_and_orchestra_gate() -> None:
    text = (SKILLS / "verify" / "references" / "phase-end.md").read_text()
    gate_section = _flat(text.split("## Phase gate", 1)[1].split("## Proof packet", 1)[0])
    assert "Run `orchestra gate <phase-slug>`" in gate_section
    assert "Exit 0 means the gate holds" in gate_section
    assert "Exit 1 lists each missing term" in gate_section
    assert "When `suite.gate` in `orchestra.toml` is `required`" in gate_section
    assert "No active `tuner:finding` for the effort has `needs` `human`" in gate_section
    assert "Fallback for reading the records by hand" in gate_section
