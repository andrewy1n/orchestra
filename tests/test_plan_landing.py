"""plan-phase records a Landing section before plan review."""

from __future__ import annotations

import re

from conftest import REPO_ROOT
from helpers import skill_text
from test_phase_landing import MERGE_STEP, PUSH_STEP, STORE_COMMIT_STEP, affirmative_matches

SKILLS = REPO_ROOT / "skills"

KEEP = (
    "branch `phase/<phase-slug>`",
    "worktree `<repo>/.worktrees/<phase-slug>`",
    "base `main`",
)


def _text(name: str) -> str:
    return skill_text(name)


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _landing_paragraph(text: str) -> str:
    flat = _flat(text)
    start = flat.find("The phase body includes a `## Landing` section")
    assert start != -1
    end = flat.find("for plan review.", start)
    assert end != -1
    return flat[start : end + len("for plan review.")]


def test_phase_body_names_landing_branch_worktree_base_and_close():
    text = _flat(_text("plan-phase"))
    for phrase in KEEP:
        assert phrase in text
    assert "No Landing → not ready for plan review. Incidental has no Landing." in text
    assert "→ merge `main` →" not in text
    assert affirmative_matches(text, MERGE_STEP) == []
    assert affirmative_matches(text, PUSH_STEP) == []
    assert affirmative_matches(text, STORE_COMMIT_STEP) == []


def test_shared_docs_name_the_same_landing():
    phrases = (
        *KEEP,
        "Incidental work has no Landing section.",
        "A phase body that omits Landing is not ready",
        "for plan review.",
    )
    for path in (
        REPO_ROOT / "shared/kinds-and-focus.md",
        SKILLS / "kinds-and-focus.md",
        REPO_ROOT / "README.md",
    ):
        doc = _landing_paragraph(path.read_text())
        for phrase in phrases:
            assert phrase in doc, path.name
        assert affirmative_matches(doc, MERGE_STEP) == [], path.name
        assert affirmative_matches(doc, PUSH_STEP) == [], path.name
        assert affirmative_matches(doc, STORE_COMMIT_STEP) == [], path.name


def test_plan_review_stays_closed_until_landing_is_present():
    flat = _flat(_text("plan-phase"))
    gate = "Open the plan review gate (skip incidental). Do not open until:"
    question_at = flat.rindex("canon create --type score:continuity-question")
    gate_at = flat.rindex(gate)
    assert gate_at < question_at
    assert "`## Landing`" in flat[gate_at:question_at]
