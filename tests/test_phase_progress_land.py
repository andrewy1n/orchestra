from __future__ import annotations

import pytest

from orchestra.canon.types import Record
from orchestra.conductor.landing.landing import LandingProofState
from orchestra.conductor.phase_progress import (
    AcceptanceHold,
    ExecutionVerdict,
    PhaseFacts,
    PhaseProgress,
    Readiness,
    TaskFact,
    VerifyFacts,
    assess,
)
from orchestra.score.planning.phase import read_phase
from orchestra.tools import Absent, BranchState, Merged, ReadFailed, Unmerged

READY = Readiness(True)


def _record() -> Record:
    return {
        "id": "rec-phase",
        "record_type": "score:phase",
        "subject": "ph",
        "payload": {"title": "Ph", "ordinal": 1, "effort": "ef"},
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-01-01T00:00:00Z",
        "body": "",
    }


def _verified(landing: LandingProofState | None, branch: BranchState | None = None) -> PhaseFacts:
    return PhaseFacts(
        phase=read_phase(_record()),
        lifecycle="active",
        spec=READY,
        design=READY,
        tasks_review=READY,
        plan=READY,
        tasks=(TaskFact("t1", "done", ExecutionVerdict("pass", "pass")),),
        acceptances=(AcceptanceHold("a1", True, True),),
        integration="not-required",
        verify=VerifyFacts("", True, (), True),
        landing=landing,
        branch=branch,
        gates=(),
        prerequisites=(),
    )


def _status(progress: PhaseProgress) -> dict[str, str]:
    return {state.stage: state.status for state in progress.stages}


def test_stale_proof_makes_land_current_with_the_stale_proof_reason() -> None:
    progress = assess(_verified("not-at-head", Merged("abc")))

    assert progress.current == "land"
    assert progress.reason == "stale-proof"
    assert _status(progress)["land"] == "current"
    assert _status(progress)["close"] == "pending"


def test_failed_landing_makes_land_current_with_the_failed_landing_reason() -> None:
    progress = assess(_verified("failed"))

    assert progress.current == "land"
    assert progress.reason == "failed-landing"
    assert _status(progress)["land"] == "current"
    assert _status(progress)["close"] == "pending"


@pytest.mark.parametrize(
    ("landing", "reason"),
    [(None, "no-landing"), ("no-landing", "no-landing"), ("no-packet", "no-packet")],
)
def test_missing_landing_keeps_land_current_with_the_landing_reason(
    landing: LandingProofState | None, reason: str
) -> None:
    progress = assess(_verified(landing))

    assert progress.current == "land"
    assert progress.reason == reason


def test_landed_phase_marks_land_done_and_close_current() -> None:
    progress = assess(_verified("landed", Merged("abc")))

    assert progress.current == "close"
    assert _status(progress)["land"] == "done"
    assert _status(progress)["close"] == "current"


def test_awaiting_merge_reason_while_the_phase_branch_is_ahead_of_main() -> None:
    progress = assess(_verified("landed", Unmerged("abc", 2)))

    assert progress.current == "close"
    assert progress.reason == "awaiting-merge"
    assert _status(progress)["close"] == "current"


@pytest.mark.parametrize("branch", [Merged("abc"), Absent()], ids=["merged", "absent"])
def test_ready_to_close_reason_when_the_phase_branch_has_nothing_ahead_of_main(
    branch: BranchState,
) -> None:
    progress = assess(_verified("landed", branch))

    assert progress.current == "close"
    assert progress.reason == "ready-to-close"
    assert _status(progress)["close"] == "current"


def test_git_read_failure_leaves_close_unknown_and_never_ready_to_close() -> None:
    progress = assess(_verified("landed", ReadFailed("git cherry: boom")))

    assert progress.current == "close"
    assert progress.reason == "git-read-failed"
    assert _status(progress)["close"] == "unknown"
    assert _status(progress)["land"] == "done"


def test_unread_branch_leaves_close_unknown() -> None:
    progress = assess(_verified("landed", None))

    assert progress.current == "close"
    assert progress.reason == "branch-unread"
    assert _status(progress)["close"] == "unknown"
