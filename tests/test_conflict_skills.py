from __future__ import annotations

from pathlib import Path

from helpers import brief_text, skill_text

ROOT = Path(__file__).resolve().parent.parent


def flat(relative: str) -> str:
    if relative == "execute brief":
        return " ".join(brief_text("execute").split())
    return " ".join((ROOT / relative).read_text(encoding="utf-8").split())


def test_execute_phase_asks_the_user_for_competing_behavior() -> None:
    for relative in (
        "skills/execute/SKILL.md",
        "execute brief",
    ):
        text = flat(relative)
        assert "need competing behavior" in text
        assert "leave the question open and ask the user" in text


def test_execute_phase_allows_resolve_only_through_the_command() -> None:
    text = flat("execute brief")
    assert "orchestra wave resolve <phase-slug> <task-slug>" in text
    assert "resolve a merge conflict outside `orchestra wave resolve`" in text


def test_plan_phase_adds_depends_on_for_tasks_that_rewrite_the_same_function() -> None:
    for text in (
        " ".join(skill_text("tasks").split()),
        flat("orchestra/conductor/briefs/sections/task-shapes.md"),
    ):
        assert "rewrite the same function" in text
        assert "depends_on" in text


def test_depends_on_same_function_rule_is_in_the_planning_rules() -> None:
    text = " ".join(skill_text("tasks").split())
    assert "Tasks that must rewrite the same function get a `depends_on` edge" in text
