"""spec, tasks, and execute carry the analyze instructions."""

from __future__ import annotations

import re

from helpers import skill_text

MARKER = "[NEEDS CLARIFICATION: <question>]"
PLAN_COMMAND = re.compile(r"(?m)^orchestra analyze <phase-slug> --stage plan[ \t]*$")
CLOSE_COMMAND = re.compile(r"(?m)^orchestra analyze <phase-slug> --stage close[ \t]*$")
EXITS_ONE = r"(?:exits?|exited|exit code) 1"


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _window(text: str, match: re.Match, radius: int = 500) -> str:
    return _flat(text[max(0, match.start() - radius) : match.end() + radius])


def test_r19_settle_phase_documents_the_marker_syntax():
    text = _flat(skill_text("spec"))
    assert MARKER in text


def test_r19_settle_phase_scopes_the_marker_to_specification_and_design_bodies():
    text = skill_text("spec")
    at = text.find(MARKER)
    assert at >= 0
    around = _flat(text[max(0, at - 600) : at + 600]).lower()
    assert "specification" in around
    assert "design" in around


def test_r19_settle_phase_requires_every_marker_resolved():
    text = _flat(skill_text("spec"))
    resolve_every = (
        r"(?i)\b(?:resolve|clear)\b[^.]{0,60}\b(?:every|each|all)\b[^.]{0,40}\bmarkers?\b"
        r"|\b(?:every|each|all)\b[^.]{0,40}\bmarkers?\b[^.]{0,60}\b(?:resolved|cleared)\b"
    )
    assert re.search(resolve_every, text)


def test_r19_settle_phase_requires_resolution_before_it_ends():
    text = _flat(skill_text("spec"))
    pattern = (
        r"(?i)\bmarkers?\b[^.]{0,120}\bbefore\b[^.]{0,60}\b(?:spec|you end|it ends|finish|done)\b"
        r"|\bbefore\b[^.]{0,60}\b(?:spec ends|you end|ending|finishing)\b[^.]{0,120}\bmarkers?\b"
    )
    assert re.search(pattern, text)


def test_r20_plan_phase_has_the_analyze_command_line():
    assert PLAN_COMMAND.search(skill_text("tasks"))


def test_r20_plan_phase_runs_analyze_before_opening_plan_review():
    text = skill_text("tasks")
    command = PLAN_COMMAND.search(text)
    assert command
    gate = text.rindex("plan-review:<current-phase-slug>")
    assert command.start() < gate


def test_r20_plan_phase_refuses_plan_review_while_analyze_exits_one():
    text = _flat(skill_text("tasks"))
    pattern = (
        rf"(?i)\brefuse\b[^.]{{0,80}}\bplan[- ]review\b[^.]{{0,120}}{EXITS_ONE}"
        rf"|{EXITS_ONE}[^.]{{0,120}}\brefuse\b[^.]{{0,80}}\bplan[- ]review\b"
    )
    assert re.search(pattern, text)


def test_r20_plan_phase_names_the_analyze_command_in_the_refusal_context():
    text = skill_text("tasks")
    command = PLAN_COMMAND.search(text)
    assert command
    assert re.search(rf"(?i)\brefuse\b[^.]{{0,200}}{EXITS_ONE}", _window(text, command, 800))


def test_r21_execute_phase_has_the_close_stage_command_line():
    assert CLOSE_COMMAND.search(skill_text("execute"))


def test_r21_execute_phase_runs_analyze_after_closing_verification_and_before_the_reviewer():
    text = skill_text("execute")
    command = CLOSE_COMMAND.search(text)
    assert command
    around = _window(text, command).lower()
    assert "closing verification" in around
    assert "reviewer" in around
    brief = text.index("orchestra review-brief --base")
    assert command.start() < brief


def test_r21_execute_phase_refuses_to_start_the_reviewer_while_analyze_exits_one():
    text = _flat(skill_text("execute"))
    pattern = (
        rf"(?i)\brefuse\b[^.]{{0,80}}\b(?:start|run|launch|spawn|dispatch)\b[^.]{{0,40}}\breviewer\b[^.]{{0,120}}{EXITS_ONE}"
        rf"|{EXITS_ONE}[^.]{{0,120}}\brefuse\b[^.]{{0,80}}\b(?:start|run|launch|spawn|dispatch)\b[^.]{{0,40}}\breviewer\b"
    )
    assert re.search(pattern, text)
