"""Tests for the shared stage list on the hub card and the phase page (R3)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from conftest import REPO_ROOT, git
from dashboard_progress_support import (
    PhaseProgress,
    assessed,
    landed_facts_on_branch,
    phase_row,
)
from test_review_stage import EFFORT, _project_with_phases

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend import stages
from dashboard.backend.progress import build_progress
from dashboard.backend.server import service
from orchestra.conductor.phase_progress import StageState, visible_stages

FULL_IDS = ["spec", "design", "tasks", "execute", "verify", "land", "close"]
LIGHT_IDS = FULL_IDS[2:]


def _states_of(stages: tuple[StageState, ...]) -> dict[str, str]:
    return {state.stage: state.status for state in stages}


def _states(progress: PhaseProgress) -> dict[str, str]:
    return _states_of(progress.stages)


def test_light_phase_lists_tasks_through_close_once_spec_and_design_are_done() -> None:
    stages = visible_stages("light", assessed("light", "verifying"))

    assert [state.stage for state in stages] == LIGHT_IDS


def test_light_phase_lists_every_stage_while_spec_or_design_is_open() -> None:
    stages = visible_stages("light", assessed("light"))

    assert [state.stage for state in stages] == FULL_IDS


def test_light_phase_keeps_the_assessed_status_of_later_stages() -> None:
    progress = assessed("light", "verifying")

    assert _states_of(visible_stages("light", progress)) == {
        "tasks": "done",
        "execute": "done",
        "verify": "current",
        "land": "pending",
        "close": "pending",
    }
    assert (progress.current, progress.reason) == ("verify", "reviewer")


def test_light_phase_with_an_open_spec_stays_at_spec_with_its_reason() -> None:
    progress = assessed("light")

    assert _states(progress)["spec"] == "current"
    assert (progress.current, progress.reason) == ("spec", "spec review is missing")


def test_light_phase_with_a_gate_on_the_open_spec_marks_spec_blocked() -> None:
    progress = assessed("light", "gated")

    assert _states(progress)["spec"] == "blocked"
    assert progress.blocked_by == ("needs-a-human",)


def test_light_phase_never_marks_a_later_stage_done_after_an_unknown_close() -> None:
    stages = visible_stages("light", assessed("light", "landed"))
    states = {state.stage: state.status for state in stages}

    assert states["land"] == "done"
    assert states["close"] == "unknown"


def test_full_phase_lists_every_stage_when_spec_and_design_are_done() -> None:
    stages = visible_stages("full", assessed("full", "verifying"))

    assert [state.stage for state in stages] == FULL_IDS


def test_light_phase_card_shows_tasks_through_close() -> None:
    card = build_progress(phase_row("light", "verifying"), [], [])

    assert [stage.id for stage in card.stages] == LIGHT_IDS


def test_light_phase_card_carries_the_current_stage_and_reason() -> None:
    card = build_progress(phase_row("light", "verifying"), [], [])

    assert (card.current, card.reason) == ("verify", "reviewer")


def test_light_phase_card_blocker_names_the_close_reason_for_an_unmerged_branch() -> None:
    card = build_progress(phase_row("light", "unmerged"), [], [])

    assert card.blockers.shown == ("close: awaiting-merge",)


@pytest.fixture()
def light_reader(tmp_path: Path) -> service.Reader:
    project, _ = _project_with_phases(tmp_path, "p")
    return service.Reader(project)


def test_light_phase_hub_card_shows_spec_as_current_while_its_review_is_open(
    light_reader: service.Reader,
) -> None:
    hub = light_reader.hub()
    card = next(item for item in hub.active_phases if item.subject == "p")

    assert card.progress is not None
    assert [stage.id for stage in card.progress.stages] == FULL_IDS
    assert card.progress.stages[0].state == "current"
    assert card.step == "spec"


def test_light_phase_page_stage_is_the_current_stage_with_its_reason(
    light_reader: service.Reader,
) -> None:
    evidence = light_reader.phase(EFFORT, "p").detail.evidence

    assert evidence is not None
    assert evidence.stage == "spec"
    assert evidence.stage_reason == "approval review is missing"


def test_light_phase_close_reason_follows_a_branch_merge_made_outside_the_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, _ = _project_with_phases(tmp_path, "p")
    root = project.project_root
    monkeypatch.setattr(stages, "phase_facts", landed_facts_on_branch(root))
    reader = service.Reader(project)

    def reasons() -> tuple[str, str]:
        card = next(item for item in reader.hub().active_phases if item.subject == "p")
        evidence = reader.phase(EFFORT, "p").detail.evidence
        assert card.progress is not None and evidence is not None
        return card.progress.reason, evidence.stage_reason

    assert reasons() == ("awaiting-merge", "awaiting-merge")
    token = reader.cache.token_only()

    git(root, "merge", "-q", "phase/p")

    assert reader.cache.token_only() == token
    assert reasons() == ("ready-to-close", "ready-to-close")
