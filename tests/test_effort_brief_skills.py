"""init writes a brief for deliver efforts only, settle-phase reads it, and the score docs list the type."""

from __future__ import annotations

import re

from conftest import REPO_ROOT
from helpers import skill_text

SCORE_AGENTS = REPO_ROOT / "orchestra" / "score" / "AGENTS.md"
CREATE_BRIEF = re.compile(r"canon create --type score:brief\b")
HEADINGS = ("## Problem", "## Users", "## Success measure", "## Non-goals")
NEGATION = re.compile(r"(?i)\b(?:no|not|never|skip|only|without|omit|does not|do not)\b")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _windows(text: str, pattern: str, before: int, after: int):
    for match in re.finditer(pattern, text):
        yield text[max(0, match.start() - before) : match.end() + after]


def test_r9_init_creates_a_brief_for_deliver_with_the_effort_slug_as_subject():
    text = _flat(skill_text("init"))
    command = re.search(r"canon create --type score:brief[ \\]+--subject [\"']?<effort-slug>", text)
    assert command
    around = text[max(0, command.start() - 600) : command.end() + 200].lower()
    assert "deliver" in around


def test_r10_init_creates_no_brief_for_repair_evaluate_or_incidental():
    text = _flat(skill_text("init"))
    assert CREATE_BRIEF.search(text)
    for window in _windows(text, r"score:brief", 400, 400):
        lower = window.lower()
        if all(kind in lower for kind in ("repair", "evaluate", "incidental")) and NEGATION.search(window):
            return
    raise AssertionError("init never excludes repair, evaluate, and incidental from the brief")


def test_r11_init_gives_a_brief_body_template_with_the_four_headings():
    text = skill_text("init")
    assert CREATE_BRIEF.search(text)
    for window in _windows(text, r"score:brief", 1500, 2500):
        if all(heading in window for heading in HEADINGS):
            return
    raise AssertionError("no score:brief body template with the four headings")


def test_r12_settle_phase_context_step_lists_the_brief_for_the_focus_effort():
    text = skill_text("settle-phase")
    start = text.index("Read context")
    step = text[start : text.index("\n3.", start)]
    assert re.search(
        r"canon list --type score:brief\b[^\n]*(?:payload\.effort=<focus>|--subject <focus>)", step,
    )


def test_r13_score_agents_lists_brief_among_the_types():
    text = _flat(SCORE_AGENTS.read_text())
    listed = re.search(r"\(([^)]*\beffort\b[^)]*)\)", text)
    assert listed
    assert re.search(r"\bbrief\b", listed.group(1))
