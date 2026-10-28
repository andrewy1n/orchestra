"""plan-phase records a Landing section before plan review."""

from __future__ import annotations

import re

from conftest import REPO_ROOT
from helpers import skill_text

SKILLS = REPO_ROOT / "skills"

LANDING_PHRASES = (
    "branch `phase/<phase-slug>`",
    "worktree `<repo>/.worktrees/<phase-slug>`",
    "base `main`",
    "commit code on the phase branch",
    "merge that branch into `main`",
    "commit the store on the primary checkout",
    "Push appears only when it is one of the human stops.",
    "Incidental work has no Landing section.",
    "A phase body that omits Landing is not ready for plan review.",
)


def _text(name: str) -> str:
    return skill_text(name)


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_phase_body_names_landing_branch_worktree_base_and_close():
    text = _flat(_text("plan-phase"))
    for phrase in LANDING_PHRASES[:3]:
        assert phrase in text
    assert "close actions (commit phase branch → merge `main` → store commit); push only as a human stop" in text
    assert "No Landing → not ready for plan review. Incidental has no Landing." in text


def test_shared_docs_name_the_same_landing():
    for path in (SKILLS / "kinds-and-focus.md", REPO_ROOT / "README.md"):
        doc = _flat(path.read_text())
        for phrase in LANDING_PHRASES:
            assert phrase in doc, path.name


def test_plan_review_stays_closed_until_landing_is_present():
    flat = _flat(_text("plan-phase"))
    gate = "Open the plan review gate (skip incidental). Do not open until:"
    question_at = flat.rindex("canon create --type score:continuity-question")
    gate_at = flat.rindex(gate)
    assert gate_at < question_at
    assert "`## Landing`" in flat[gate_at:question_at]
