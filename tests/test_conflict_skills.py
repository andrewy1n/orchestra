from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def flat(relative: str) -> str:
    return " ".join((ROOT / relative).read_text(encoding="utf-8").split())


def test_execute_phase_asks_the_user_for_competing_behavior() -> None:
    for relative in (
        "skills/execute-phase/SKILL.md",
        "skills/execute-phase/references/mechanics.md",
    ):
        text = flat(relative)
        assert "need competing behavior" in text
        assert "leave the question open and ask the user" in text


def test_execute_phase_allows_resolve_only_through_the_command() -> None:
    text = flat("skills/execute-phase/SKILL.md")
    assert "orchestra wave resolve <phase-slug> <task-slug>" in text
    assert "resolve a merge conflict outside `orchestra wave resolve`" in text


def test_plan_phase_adds_depends_on_for_tasks_that_rewrite_the_same_function() -> None:
    for relative in (
        "skills/plan-phase/SKILL.md",
        "skills/plan-phase/references/task-shapes.md",
    ):
        text = flat(relative)
        assert "rewrite the same function" in text
        assert "depends_on" in text


def test_depends_on_same_function_rule_is_in_the_planning_rules() -> None:
    text = flat("skills/plan-phase/SKILL.md")
    assert "Tasks that must rewrite the same function get a `depends_on` edge" in text
