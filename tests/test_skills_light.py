from __future__ import annotations

from helpers import skill_text


def test_settle_phase_sets_weight_light_for_a_small_phase() -> None:
    text = skill_text("spec")
    assert "about 4 tasks or fewer" in " ".join(text.split())
    assert "no option changes the architecture" in " ".join(text.split())
    assert "weight` on the phase" in text


def test_settle_phase_lets_the_user_override_the_weight_either_way() -> None:
    assert "let the user override it either way" in " ".join(skill_text("spec").split())


def test_light_nospec_settle_phase_writes_no_specification_or_design() -> None:
    text = skill_text("spec")
    assert "writes no `score:specification` and no `score:design`" in text.replace("\n  ", " ")
    assert "For a full phase" in " ".join(text.split())


def test_settle_phase_writes_a_decision_in_a_light_phase_only_for_a_user_choice() -> None:
    text = skill_text("spec").replace("\n  ", " ")
    assert "Write a decision only when the user picked between options" in " ".join(text.split())


def test_plan_phase_keeps_the_plan_review_gate_unless_autonomy_skips_it() -> None:
    text = skill_text("tasks").replace("\n    ", " ")
    assert "Skip this gate at `auto-plan` and `auto-phases`" in " ".join(text.split())
    assert "Only an explicit `gated` creates a blocking" in " ".join(text.split())


def test_light_phase_keeps_verification_reviewer_oracles_and_red_first() -> None:
    text = skill_text("spec").replace("\n  ", " ")
    flat = " ".join(text.split())
    assert (
        "Verification, the reviewer, selected frozen oracles, and TDD red-first stay the same"
        in flat
    )


def test_plan_phase_allows_a_multi_requirement_acceptance_in_a_light_phase() -> None:
    text = skill_text("tasks").replace("\n  ", " ")
    assert "one acceptance with a `requirements` array" in " ".join(text.split())
