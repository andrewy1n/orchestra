"""Tests for the shared stage list on the hub card and the phase page (R3)."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest
from conftest import REPO_ROOT, git
from test_review_stage import EFFORT, _project_with_phases

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend import stages
from dashboard.backend.phase import PhaseEvidence, PhaseRow
from dashboard.backend.progress import build_progress
from dashboard.backend.server import service
from dashboard.backend.stages import surface_progress
from orchestra.canon.types import Record
from orchestra.conductor.phase_progress import (
    STAGES,
    AcceptanceHold,
    ExecutionVerdict,
    HumanGateFact,
    PhaseFacts,
    PhaseProgress,
    Readiness,
    TaskFact,
    VerifyFacts,
    assess,
)
from orchestra.score.phase import Phase, read_phase
from orchestra.tools import Unmerged, branch_state

FULL_IDS = list(STAGES)
LIGHT_IDS = ["tasks", "execute", "verify", "land", "close"]
READY = Readiness(True)


def _record(weight: str) -> Record:
    return {
        "id": "rec-phase",
        "record_type": "score:phase",
        "subject": "ph",
        "payload": {"title": "Ph", "ordinal": 1, "effort": "ef", "weight": weight},
        "lifecycle_state": "in_progress",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-01-01T00:00:00Z",
        "body": "",
    }


def _facts(weight: str) -> PhaseFacts:
    return PhaseFacts(
        phase=read_phase(_record(weight)),
        lifecycle="in_progress",
        spec=Readiness(False, "spec review is missing"),
        design=Readiness(False, "design review is missing"),
        tasks_review=Readiness(False, "tasks review is missing"),
        plan=Readiness(False, "task plan is not ready"),
        tasks=(),
        acceptances=(),
        integration="not-required",
        verify=None,
        landing=None,
        branch=None,
        gates=(),
        prerequisites=(),
    )


def _executed(weight: str) -> PhaseFacts:
    return replace(
        _facts(weight),
        spec=READY,
        design=READY,
        tasks_review=READY,
        plan=READY,
        tasks=(TaskFact("t1", "done", ExecutionVerdict("pass", "pass")),),
        acceptances=(AcceptanceHold("a1", True, True),),
    )


def _row(weight: str, progress: PhaseProgress) -> PhaseRow:
    return PhaseRow(
        subject="ph",
        title="Ph",
        ordinal=1,
        state="in_progress",
        done=1,
        total=1,
        evidence=PhaseEvidence(
            phase="ph",
            weight=weight,
            requirements=(),
            stage="",
            integration=None,
            release_ready=False,
            decisions=(),
            non_goals="",
        ),
        progress=progress,
    )


def _states(progress: PhaseProgress) -> dict[str, str]:
    return {state.stage: state.status for state in progress.stages}


def test_light_phase_surface_lists_tasks_through_close() -> None:
    surface = surface_progress("light", assess(_facts("light")))

    assert [state.stage for state in surface.stages] == LIGHT_IDS


def test_full_phase_surface_lists_all_seven_stages() -> None:
    surface = surface_progress("full", assess(_facts("full")))

    assert [state.stage for state in surface.stages] == FULL_IDS


def test_light_phase_surface_keeps_the_assessed_status_of_later_stages() -> None:
    facts = replace(
        _executed("light"),
        verify=VerifyFacts("", False, (), False),
    )

    surface = surface_progress("light", assess(facts))

    assert _states(surface) == {
        "tasks": "done",
        "execute": "done",
        "verify": "current",
        "land": "pending",
        "close": "pending",
    }
    assert (surface.current, surface.reason) == ("verify", "reviewer")


def test_light_phase_surface_marks_tasks_current_while_spec_or_design_is_open() -> None:
    surface = surface_progress("light", assess(_facts("light")))

    assert _states(surface)["tasks"] == "current"
    assert surface.current == "tasks"
    assert surface.reason == "spec review is missing"


def test_light_phase_surface_marks_tasks_blocked_while_a_gate_blocks_the_open_spec() -> None:
    facts = replace(_facts("light"), gates=(HumanGateFact("needs-a-human"),))

    surface = surface_progress("light", assess(facts))

    assert _states(surface)["tasks"] == "blocked"
    assert surface.blocked_by == ("needs-a-human",)


def test_light_phase_surface_never_marks_a_later_stage_done_after_an_unknown_close() -> None:
    facts = replace(_executed("light"), verify=VerifyFacts("", True, (), True), landing="landed")

    surface = surface_progress("light", assess(facts))

    assert _states(surface)["land"] == "done"
    assert _states(surface)["close"] == "unknown"


def test_light_phase_card_shows_tasks_through_close() -> None:
    surface = assess(replace(_executed("light"), verify=VerifyFacts("", False, (), False)))

    card = build_progress(_row("light", surface), [], [])

    assert [stage.id for stage in card.stages] == LIGHT_IDS


def test_full_phase_card_shows_all_seven_stages() -> None:
    surface = assess(replace(_executed("full"), verify=VerifyFacts("", False, (), False)))

    card = build_progress(_row("full", surface), [], [])

    assert [stage.id for stage in card.stages] == FULL_IDS


def test_light_phase_card_carries_the_current_stage_and_reason() -> None:
    surface = assess(replace(_executed("light"), verify=VerifyFacts("", False, (), False)))

    card = build_progress(_row("light", surface), [], [])

    assert (card.current, card.reason) == ("verify", "reviewer")


def test_light_phase_card_blocker_names_the_close_reason_for_an_unmerged_branch() -> None:
    facts = replace(
        _executed("light"),
        verify=VerifyFacts("", True, (), True),
        landing="landed",
        branch=Unmerged("abc", 2),
    )

    card = build_progress(_row("light", assess(facts)), [], [])

    assert card.blockers.shown == ("close: awaiting-merge",)


@pytest.fixture()
def light_reader(tmp_path: Path) -> service.Reader:
    project, _ = _project_with_phases(tmp_path, "p")
    return service.Reader(project)


def test_light_phase_hub_card_shows_tasks_through_close(light_reader: service.Reader) -> None:
    hub = light_reader.hub()
    card = next(item for item in hub.active_phases if item.subject == "p")

    assert card.progress is not None
    assert [stage.id for stage in card.progress.stages] == LIGHT_IDS
    assert card.progress.stages[0].state == "current"
    assert card.step == "tasks"


def test_light_phase_page_stage_is_the_current_stage_with_its_reason(
    light_reader: service.Reader,
) -> None:
    evidence = light_reader.phase(EFFORT, "p").detail.evidence

    assert evidence is not None
    assert evidence.stage == "tasks"
    assert evidence.stage_reason == "approval review is missing"


def test_light_phase_close_reason_follows_a_branch_merge_made_outside_the_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, _ = _project_with_phases(tmp_path, "p")
    root = project.project_root

    def landed_facts(_target: object, _records: object, phase: Phase) -> PhaseFacts:
        return replace(
            _executed("light"),
            phase=phase,
            verify=VerifyFacts("", True, (), True),
            landing="landed",
            branch=branch_state(root, f"phase/{phase.subject}", "main"),
        )

    monkeypatch.setattr(stages, "phase_facts", landed_facts)
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
