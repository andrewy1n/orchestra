from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon.types import Record
from orchestra.conductor.phases.progress.phase_progress import (
    STAGES,
    AcceptanceHold,
    ExecutionVerdict,
    HumanGateFact,
    IntegrationState,
    PhaseFacts,
    PhaseProgress,
    PrerequisiteFact,
    Readiness,
    TaskFact,
    VerifyFacts,
    assess,
    phase_facts,
)
from orchestra.score.planning.phase import read_phase

READY = Readiness(True)
PASSING = ExecutionVerdict("pass", "pass")


def _record(lifecycle: str) -> Record:
    return {
        "id": "rec-phase",
        "record_type": "score:phase",
        "subject": "ph",
        "payload": {"title": "Ph", "ordinal": 1, "effort": "ef"},
        "lifecycle_state": lifecycle,
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-01-01T00:00:00Z",
        "body": "",
    }


def _facts(lifecycle: str = "active") -> PhaseFacts:
    return PhaseFacts(
        phase=read_phase(_record(lifecycle)),
        lifecycle=lifecycle,
        spec=Readiness(False, "spec review is missing"),
        design=Readiness(False, "design review is missing"),
        tasks_review=Readiness(False, "tasks review is missing"),
        plan=Readiness(False, "analyzed task plan requires work-items"),
        tasks=(),
        acceptances=(),
        integration="not-required",
        verify=None,
        landing=None,
        branch=None,
        gates=(),
        prerequisites=(),
    )


def _planned() -> PhaseFacts:
    return replace(_facts(), spec=READY, design=READY, tasks_review=READY, plan=READY)


def _executed() -> PhaseFacts:
    return replace(
        _planned(),
        tasks=(TaskFact("t1", "done", PASSING),),
        acceptances=(AcceptanceHold("a1", True, True),),
    )


def _verifying(verify: VerifyFacts) -> PhaseFacts:
    return replace(_executed(), verify=verify)


COMPLETE = VerifyFacts("", True, (), True)


def _status(progress: PhaseProgress) -> dict[str, str]:
    return {state.stage: state.status for state in progress.stages}


def test_stage_list_names_the_seven_stages_in_order() -> None:
    progress = assess(_facts())

    assert [state.stage for state in progress.stages] == [
        "spec",
        "design",
        "tasks",
        "execute",
        "verify",
        "land",
        "close",
    ]
    assert tuple(state.stage for state in progress.stages) == STAGES


def test_stage_list_marks_the_first_unfinished_stage_current_and_the_rest_pending() -> None:
    progress = assess(replace(_facts(), spec=READY))

    assert progress.current == "design"
    assert _status(progress) == {
        "spec": "done",
        "design": "current",
        "tasks": "pending",
        "execute": "pending",
        "verify": "pending",
        "land": "pending",
        "close": "pending",
    }
    assert progress.reason == "design review is missing"


def test_stage_list_never_marks_a_stage_after_the_current_stage_done() -> None:
    facts = replace(_facts(), design=READY, tasks_review=READY, plan=READY)

    progress = assess(replace(facts, landing="landed"))

    assert progress.current == "spec"
    assert _status(progress) == {
        "spec": "current",
        "design": "pending",
        "tasks": "pending",
        "execute": "pending",
        "verify": "pending",
        "land": "pending",
        "close": "pending",
    }


def test_stage_list_tasks_stage_waits_for_the_plan_as_well_as_the_review() -> None:
    facts = replace(_facts(), spec=READY, design=READY, tasks_review=READY)

    progress = assess(facts)

    assert progress.current == "tasks"
    assert progress.reason == "analyzed task plan requires work-items"


def test_stage_list_execute_names_the_task_that_is_not_done() -> None:
    facts = replace(_planned(), tasks=(TaskFact("t1", "in_progress", None),))

    progress = assess(facts)

    assert progress.current == "execute"
    assert progress.reason == "task 't1' is not done"


@pytest.mark.parametrize(
    ("verify", "acceptances", "integration", "step"),
    [
        (None, (), "not-required", "analyze"),
        (None, (AcceptanceHold("a1", False, False),), "not-required", "analyze"),
        (None, (AcceptanceHold("a1", True, False),), "not-required", "analyze"),
        (VerifyFacts("suite has not passed", True, (), True), None, None, "suite"),
        (VerifyFacts("", False, (), True), None, None, "reviewer"),
        (COMPLETE, None, "missing", "integration-report"),
        (COMPLETE, None, "failing", "integration-report"),
        (VerifyFacts("", True, ("missing verification-task-done",), True), None, None, "gate"),
        (VerifyFacts("", True, (), False), None, None, "proof"),
    ],
    ids=[
        "no-acceptances",
        "acceptance-without-run",
        "acceptance-not-passing",
        "suite",
        "reviewer",
        "integration-missing",
        "integration-failing",
        "gate",
        "proof",
    ],
)
def test_verify_reason_names_the_open_verify_step(
    verify: VerifyFacts | None,
    acceptances: tuple[AcceptanceHold, ...] | None,
    integration: IntegrationState | None,
    step: str,
) -> None:
    facts = replace(_executed(), verify=verify or COMPLETE)
    if acceptances is not None:
        facts = replace(facts, acceptances=acceptances)
    if integration is not None:
        facts = replace(facts, integration=integration)

    progress = assess(facts)

    assert progress.current == "verify"
    assert progress.reason == step
    assert _status(progress)["verify"] == "current"


def test_verify_reason_is_unknown_when_verify_facts_were_not_read() -> None:
    progress = assess(replace(_executed(), verify=None))

    assert progress.current == "verify"
    assert _status(progress)["verify"] == "unknown"


def test_verify_reason_is_empty_once_every_verify_step_holds() -> None:
    progress = assess(_verifying(COMPLETE))

    assert progress.current == "land"
    assert _status(progress)["verify"] == "done"


def test_human_gate_blocks_the_current_stage_and_names_every_gate_subject() -> None:
    facts = replace(_planned(), gates=(HumanGateFact("q-one"), HumanGateFact("f-two")))

    progress = assess(facts)

    assert progress.current == "execute"
    assert _status(progress)["execute"] == "blocked"
    assert progress.blocked_by == ("q-one", "f-two")
    assert "q-one" in progress.reason
    assert "f-two" in progress.reason


def test_human_gate_blocks_a_phase_that_has_not_started() -> None:
    progress = assess(replace(_facts(), gates=(HumanGateFact("q-one"),)))

    assert progress.current == "spec"
    assert _status(progress)["spec"] == "blocked"


def test_human_gate_does_not_block_a_done_phase() -> None:
    progress = assess(replace(_facts("done"), gates=(HumanGateFact("q-one"),)))

    assert progress.blocked_by == ()
    assert set(_status(progress).values()) == {"done"}


def test_prerequisite_not_done_blocks_the_current_stage_and_names_it() -> None:
    facts = replace(
        _planned(),
        prerequisites=(PrerequisiteFact("base", "active"), PrerequisiteFact("older", "done")),
    )

    progress = assess(facts)

    assert _status(progress)["execute"] == "blocked"
    assert progress.blocked_by == ("base",)
    assert "base" in progress.reason


def test_prerequisite_done_leaves_the_phase_unblocked() -> None:
    facts = replace(_planned(), prerequisites=(PrerequisiteFact("base", "done"),))

    progress = assess(facts)

    assert progress.blocked_by == ()
    assert _status(progress)["execute"] == "current"


def test_prerequisite_and_human_gate_are_both_named() -> None:
    facts = replace(
        _planned(),
        gates=(HumanGateFact("q-one"),),
        prerequisites=(PrerequisiteFact("base", "active"),),
    )

    progress = assess(facts)

    assert set(progress.blocked_by) == {"q-one", "base"}


def test_lifecycle_done_reports_every_stage_done() -> None:
    progress = assess(_facts("done"))

    assert [state.stage for state in progress.stages] == list(STAGES)
    assert {state.status for state in progress.stages} == {"done"}
    assert progress.current is None
    assert progress.blocked_by == ()


def test_lifecycle_done_ignores_prerequisites_and_missing_evidence() -> None:
    facts = replace(_facts("done"), prerequisites=(PrerequisiteFact("base", "active"),))

    progress = assess(facts)

    assert {state.status for state in progress.stages} == {"done"}


def test_lifecycle_active_after_landing_leaves_close_current() -> None:
    progress = assess(replace(_verifying(COMPLETE), landing="landed"))

    assert progress.current == "close"
    assert _status(progress)["land"] == "done"


def test_assess_is_deterministic() -> None:
    facts = _verifying(VerifyFacts("", True, ("missing x",), True))

    assert assess(facts) == assess(facts)


def test_phase_facts_reads_prerequisites_and_skips_verify_reads_before_verify(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", "ef", {"goal": "g", "kind": "deliver"})
    create(project, "score:phase", "base", {"title": "Base", "ordinal": 1, "effort": "ef"})
    create(
        project,
        "score:phase",
        "ph",
        {"title": "Ph", "ordinal": 2, "effort": "ef", "depends_on": ["base"]},
    )
    records = project.records()
    phase = read_phase(next(r for r in records if r["subject"] == "ph"))

    facts = phase_facts(project, records, phase)

    assert facts.prerequisites == (PrerequisiteFact("base", "planned"),)
    assert facts.verify is None
    assert facts.branch is None
    progress = assess(facts)
    assert progress.current == "spec"
    assert progress.blocked_by == ("base",)
    assert _status(progress)["spec"] == "blocked"
