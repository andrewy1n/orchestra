from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from conductor_support import write_policy
from test_workflow_phase_progress import (
    BODY,
    _actions,
    _execution_report,
    _passing_acceptance,
    _phase,
    _plan,
    _project,
    _review,
)

from orchestra.canon.types import Record
from orchestra.conductor import phase_progress
from orchestra.conductor.phase_progress import (
    AcceptanceHold,
    ExecutionVerdict,
    PhaseFacts,
    Readiness,
    TaskFact,
    VerifyFacts,
    assess,
)
from orchestra.conductor.workflow import step_stage
from orchestra.score.planning.phase import current_phase_model, read_phase
from orchestra.tools import Unmerged

READY = Readiness(True)
LANDING_BODY = BODY + "## Landing\nBranch phase/p1.\n"


def _record(body: str) -> Record:
    return {
        "id": "rec-phase",
        "record_type": "score:phase",
        "subject": "ph",
        "payload": {"title": "Ph", "ordinal": 1, "effort": "ef"},
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-01-01T00:00:00Z",
        "body": body,
    }


def _verified(body: str = BODY) -> PhaseFacts:
    return PhaseFacts(
        phase=read_phase(_record(body)),
        lifecycle="active",
        spec=READY,
        design=READY,
        tasks_review=READY,
        plan=READY,
        tasks=(TaskFact("t1", "done", ExecutionVerdict("pass", "pass")),),
        acceptances=(AcceptanceHold("a1", True, True),),
        integration="not-required",
        verify=VerifyFacts("", True, (), True),
        landing=None,
        branch=None,
        gates=(),
        prerequisites=(),
        has_landing="## Landing" in body,
    )


def _status(facts: PhaseFacts) -> dict[str, str]:
    return {state.stage: state.status for state in assess(facts).stages}


def test_landless_phase_past_verify_marks_land_done_and_close_current() -> None:
    progress = assess(_verified())

    assert progress.current == "close"
    assert progress.reason == "ready-to-close"
    assert {state.stage: state.status for state in progress.stages}["land"] == "done"
    assert _status(_verified())["close"] == "current"


def test_landless_phase_ignores_branch_state() -> None:
    facts = replace(_verified(), branch=Unmerged("abc", 2))

    assert assess(facts).reason == "ready-to-close"


def test_landless_phase_before_verify_completes_keeps_verify_current() -> None:
    facts = replace(_verified(), verify=VerifyFacts("", False, (), True))

    progress = assess(facts)

    assert progress.current == "verify"
    assert _status(facts)["land"] == "pending"


def test_landed_phase_without_landing_proof_keeps_land_current() -> None:
    progress = assess(_verified(LANDING_BODY))

    assert progress.current == "land"
    assert progress.reason == "no-landing"


@pytest.mark.parametrize(
    ("body", "has_landing"), [(BODY, False), (LANDING_BODY, True)], ids=["landless", "landed"]
)
def test_phase_facts_carry_whether_the_body_has_a_landing_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str, has_landing: bool
) -> None:
    project = _project(tmp_path)
    _phase(project, "p1", 1, body)
    records = project.records()
    model = current_phase_model("p1", records)
    assert model is not None
    monkeypatch.setattr(
        phase_progress, "verify_facts", lambda *_args, **_kwargs: VerifyFacts("", True, (), True)
    )

    facts = phase_progress.phase_facts(project, records, model)

    assert facts.has_landing is has_landing


def test_workflow_treats_the_land_step_of_a_landless_phase_as_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _project(tmp_path)
    write_policy(project.project_root)
    _phase(project, "p1", 1)
    _plan(project, "p1")
    for step in ("spec", "design", "tasks"):
        _review(project, "p1", step)
    _execution_report(project, "p1", "pass")
    _passing_acceptance(project, "p1")
    monkeypatch.setattr(
        phase_progress, "verify_facts", lambda *_args, **_kwargs: VerifyFacts("", True, (), True)
    )

    actions = _actions(project, "p1", "single-step", "land")

    assert actions == ()
    assert step_stage(project, project.records(), "p1", "land") == "close"
