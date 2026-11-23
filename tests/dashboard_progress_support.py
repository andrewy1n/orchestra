from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Literal

from dashboard.backend.phase import PhaseEvidence, PhaseRow
from orchestra.canon.types import Record
from orchestra.conductor.phase_progress import (
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
from orchestra.score.planning.phase import Phase, read_phase
from orchestra.tools import Unmerged, branch_state

Scenario = Literal["fresh", "gated", "verifying", "landed", "unmerged"]

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


def _scenario_facts(weight: str, scenario: Scenario) -> PhaseFacts:
    if scenario == "fresh":
        return _facts(weight)
    if scenario == "gated":
        return replace(_facts(weight), gates=(HumanGateFact("needs-a-human"),))
    if scenario == "verifying":
        return replace(_executed(weight), verify=VerifyFacts("", False, (), False))
    landed = replace(_executed(weight), verify=VerifyFacts("", True, (), True), landing="landed")
    if scenario == "landed":
        return landed
    return replace(landed, branch=Unmerged("abc", 2))


def assessed(weight: str, scenario: Scenario = "fresh") -> PhaseProgress:
    return assess(_scenario_facts(weight, scenario))


def phase_row(weight: str, scenario: Scenario = "fresh") -> PhaseRow:
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
        progress=assessed(weight, scenario),
    )


def landed_facts_on_branch(root: Path) -> Callable[[object, object, Phase], PhaseFacts]:
    def landed_facts(_target: object, _records: object, phase: Phase) -> PhaseFacts:
        return replace(
            _scenario_facts("light", "landed"),
            phase=phase,
            branch=branch_state(root, f"phase/{phase.subject}", "main"),
        )

    return landed_facts
