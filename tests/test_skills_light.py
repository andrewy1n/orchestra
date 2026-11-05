from __future__ import annotations

from helpers import skill_text


def test_settle_phase_sets_weight_light_for_a_small_phase() -> None:
    text = skill_text("settle-phase")
    assert "about 4\n  tasks or fewer" in text
    assert "no option changes the architecture" in text
    assert "`weight` on the phase" in text


def test_settle_phase_lets_the_user_override_the_weight_either_way() -> None:
    assert "let the user override it either way" in skill_text("settle-phase").replace("\n  ", " ")


def test_light_nospec_settle_phase_writes_no_specification_or_design() -> None:
    text = skill_text("settle-phase")
    assert "writes no `score:specification` and no `score:design`" in text.replace("\n  ", " ")
    assert "Full structured work only (skip for a light phase)" in text.replace("\n   ", " ")


def test_settle_phase_writes_a_decision_in_a_light_phase_only_for_a_user_choice() -> None:
    text = skill_text("settle-phase").replace("\n  ", " ")
    assert "only when the user picked between options" in text


def test_plan_phase_keeps_the_plan_review_gate_unless_autonomy_skips_it() -> None:
    text = skill_text("plan-phase").replace("\n    ", " ")
    assert "autonomy setting may skip this gate for a light phase" in text
    assert "the gate stays on" in text


def test_light_phase_keeps_verification_reviewer_oracles_and_red_first() -> None:
    text = skill_text("settle-phase").replace("\n  ", " ")
    assert "Verification, the reviewer, frozen oracles, and red-first stay the same" in text


def test_plan_phase_allows_a_multi_requirement_acceptance_in_a_light_phase() -> None:
    text = skill_text("plan-phase").replace("\n  ", " ")
    assert "one acceptance may carry `requirements`" in text
