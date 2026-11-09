"""Tests for phase progress stages (R5, R6, R7)."""

from __future__ import annotations

import sys

import pytest
from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend.progress import derive_stages

FULL_IDS = ["spec", "design", "tasks", "execute", "verify", "review", "land", "close"]
LIGHT_IDS = ["tasks", "execute", "verify", "review", "land", "close"]

ALL_DONE = {
    "weight": "full",
    "phase_state": "done",
    "approved": frozenset({"spec", "design", "plan"}),
    "task_states": ("done", "done"),
    "requirement_statuses": ("verified", "verified"),
    "review_passed_at_head": True,
    "branch_merged": True,
}


def _stages(**overrides):
    return derive_stages(**{**ALL_DONE, **overrides})


def _states(**overrides) -> dict[str, str]:
    return {stage.id: stage.state for stage in _stages(**overrides)}


def _current(**overrides) -> str | None:
    current = [stage.id for stage in _stages(**overrides) if stage.state == "current"]
    assert len(current) <= 1
    return current[0] if current else None


def _in_progress(**overrides):
    base = {
        "phase_state": "in_progress",
        "approved": frozenset(),
        "task_states": (),
        "requirement_statuses": ("unverified",),
        "review_passed_at_head": False,
        "branch_merged": False,
    }
    return {**base, **overrides}


def test_r5_lists_eight_stages_in_order() -> None:
    stages = _stages(**_in_progress())
    assert [stage.id for stage in stages] == FULL_IDS


def test_r5_nothing_done_marks_first_stage_current_and_rest_pending() -> None:
    states = [stage.state for stage in _stages(**_in_progress())]
    assert states == ["current"] + ["pending"] * 7


def test_r5_states_are_done_current_or_pending() -> None:
    stages = _stages(**_in_progress(approved=frozenset({"spec"})))
    assert {stage.state for stage in stages} == {"done", "current", "pending"}


def test_r5_exactly_one_current_with_done_stages_before_it() -> None:
    stages = _stages(
        **_in_progress(
            approved=frozenset({"spec", "design", "plan"}),
            task_states=("done", "in_progress"),
        )
    )
    states = [stage.state for stage in stages]
    assert states.count("current") == 1
    assert states == ["done", "done", "done", "current", "pending", "pending", "pending", "pending"]


def test_r5_finished_phase_has_every_stage_done_and_no_current() -> None:
    stages = _stages()
    assert [stage.id for stage in stages] == FULL_IDS
    assert {stage.state for stage in stages} == {"done"}


def test_r6_light_phase_omits_spec_and_design() -> None:
    stages = _stages(**_in_progress(weight="light"))
    assert [stage.id for stage in stages] == LIGHT_IDS


def test_r6_light_phase_has_six_stages_and_first_is_current() -> None:
    stages = _stages(**_in_progress(weight="light"))
    assert len(stages) == 6
    assert stages[0].state == "current"


def test_r6_light_phase_ignores_missing_spec_and_design_approval() -> None:
    states = _states(**_in_progress(weight="light", approved=frozenset({"plan"})))
    assert states["tasks"] == "done"
    assert states["execute"] == "current"


def test_r6_full_phase_keeps_spec_and_design() -> None:
    assert [stage.id for stage in _stages(weight="full")] == FULL_IDS


@pytest.mark.parametrize(
    ("stage", "approved", "expected"),
    [
        ("spec", frozenset({"spec"}), "done"),
        ("spec", frozenset({"design", "plan"}), "pending"),
        ("design", frozenset({"design"}), "done"),
        ("design", frozenset({"spec", "plan"}), "pending"),
        ("tasks", frozenset({"plan"}), "done"),
        ("tasks", frozenset({"spec", "design"}), "pending"),
    ],
)
def test_r7_approval_stages_follow_approved_records(stage, approved, expected) -> None:
    states = _states(**_in_progress(approved=approved))
    assert (states[stage] == "done") is (expected == "done")


def test_r7_execute_done_when_every_task_done() -> None:
    states = _states(**_in_progress(task_states=("done", "done", "done")))
    assert states["execute"] == "done"


@pytest.mark.parametrize("task_states", [("done", "in_progress"), ("done", "planned"), ()])
def test_r7_execute_not_done_when_a_task_is_open_or_absent(task_states) -> None:
    states = _states(**_in_progress(task_states=task_states))
    assert states["execute"] != "done"


def test_r7_verify_done_when_every_requirement_verified() -> None:
    states = _states(**_in_progress(requirement_statuses=("verified", "verified")))
    assert states["verify"] == "done"


@pytest.mark.parametrize(
    "statuses", [("verified", "unverified"), ("verified", "failing"), ("unverified",)]
)
def test_r7_verify_not_done_when_a_requirement_is_not_proven(statuses) -> None:
    states = _states(**_in_progress(requirement_statuses=statuses))
    assert states["verify"] != "done"


def test_r7_review_done_with_passing_review_at_head() -> None:
    assert _states(**_in_progress(review_passed_at_head=True))["review"] == "done"


def test_r7_review_not_done_without_passing_review_at_head() -> None:
    assert _states(**_in_progress(review_passed_at_head=False))["review"] != "done"


def test_r7_land_done_when_branch_merged() -> None:
    assert _states(**_in_progress(branch_merged=True))["land"] == "done"


def test_r7_land_not_done_when_branch_unmerged() -> None:
    assert _states(**_in_progress(branch_merged=False))["land"] != "done"


def test_r7_close_done_when_phase_done() -> None:
    assert _states(**_in_progress(phase_state="done"))["close"] == "done"


def test_r7_close_not_done_when_phase_in_progress() -> None:
    assert _states(**_in_progress(phase_state="in_progress"))["close"] != "done"


def test_r7_current_is_first_stage_not_done() -> None:
    assert _current(**_in_progress()) == "spec"
    assert _current(**_in_progress(approved=frozenset({"spec"}))) == "design"
    assert _current(**_in_progress(approved=frozenset({"spec", "design"}))) == "tasks"
    approved = frozenset({"spec", "design", "plan"})
    assert _current(**_in_progress(approved=approved)) == "execute"
    done_tasks = ("done",)
    assert _current(**_in_progress(approved=approved, task_states=done_tasks)) == "verify"
    proven = ("verified",)
    assert (
        _current(
            **_in_progress(approved=approved, task_states=done_tasks, requirement_statuses=proven)
        )
        == "review"
    )


def test_r7_current_skips_back_to_earliest_gap_when_later_stages_are_done() -> None:
    assert _current(approved=frozenset({"design", "plan"})) == "spec"
    assert _current(task_states=("done", "planned")) == "execute"
    assert _current(branch_merged=False, phase_state="in_progress") == "land"
    states = _states(approved=frozenset({"design", "plan"}))
    assert states["spec"] == "current"
    assert states["design"] == "done"
    assert states["close"] == "done"


def test_r7_land_is_current_after_review_passes_and_branch_unmerged() -> None:
    assert _current(**{**ALL_DONE, "branch_merged": False, "phase_state": "in_progress"}) == "land"


def test_r7_close_is_current_after_land() -> None:
    assert _current(phase_state="in_progress") == "close"
