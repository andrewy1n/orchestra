from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import Record
from orchestra.conductor.verification.evidence import head_evidence
from orchestra.conductor.verification.evidence.head_evidence import EvidenceIndex
from orchestra.conductor.verification.requirements import (
    UNVERIFIED,
    VERIFIED,
    RequirementState,
)
from orchestra.score.planning.standing_constraint import RECORD_TYPE

VIOLATED = "violated"
INCONCLUSIVE = "inconclusive"
Outcome = RequirementState | Literal["violated", "inconclusive"]


@dataclass(frozen=True)
class ConstraintOutcome:
    name: str
    area: str
    pinned_id: str
    outcome: Outcome
    check_run_id: str | None
    evidence: str
    newer_id: str | None


@dataclass(frozen=True)
class ConstraintResult:
    outcome: Outcome
    constraint_id: str
    revision: str


def _run_outcome(holds: bool, run: Record) -> Outcome:
    if holds:
        return VERIFIED
    return VIOLATED if run["payload"].get("result") == "fail" else INCONCLUSIVE


def criterion_id(constraint_id: str) -> str:
    return f"standing-constraint:{constraint_id}"


def pinned_constraint_ids(records: Sequence[Record], phase: str) -> list[str]:
    ids: list[str] = []
    for record in records:
        if (
            record["record_type"] == "score:design"
            and record["lifecycle_state"] == "active"
            and record["payload"].get("phase") == phase
        ):
            pinned = record["payload"].get("standing_constraints", [])
            if isinstance(pinned, list):
                ids.extend(item for item in pinned if isinstance(item, str))
    return list(dict.fromkeys(ids))


def _newer_id(records: Sequence[Record], pinned: Record) -> str | None:
    for record in records:
        if (
            record["record_type"] == RECORD_TYPE
            and record["lifecycle_state"] == "active"
            and record["subject"] == pinned["subject"]
            and record["id"] != pinned["id"]
        ):
            return record["id"]
    return None


def _evidence(run: Record) -> str:
    body = run.get("body")
    return body if isinstance(body, str) else ""


def standing_constraint_status(
    records: Sequence[Record], phase: str, head: str | None
) -> list[ConstraintOutcome]:
    index = EvidenceIndex(records)
    by_id = {record["id"]: record for record in records}
    outcomes: list[ConstraintOutcome] = []
    for pinned_id in pinned_constraint_ids(records, phase):
        pinned = by_id.get(pinned_id)
        if pinned is None or pinned["record_type"] != RECORD_TYPE:
            raise RecordShapeError(
                pinned_id, "standing_constraints", "pin does not resolve to a standing constraint"
            )
        run: Record | None = None
        reason = "no revision to check against"
        outcome: Outcome = UNVERIFIED
        if head is not None:
            answer = head_evidence.criterion_runner_at_head(index, criterion_id(pinned_id), head)
            run, reason = answer.run, answer.reason
            if run is not None:
                outcome = VERIFIED if answer.holds else "violated"
        outcomes.append(
            ConstraintOutcome(
                name=pinned["subject"],
                area=str(pinned["payload"].get("area", "")),
                pinned_id=pinned_id,
                outcome=outcome,
                check_run_id=run["id"] if run is not None else None,
                evidence=_evidence(run) if run is not None else reason,
                newer_id=_newer_id(records, pinned),
            )
        )
    return outcomes


def constraint_outcomes(
    records: Sequence[Record], constraint_ids: Sequence[str], revision: str
) -> list[ConstraintResult]:
    index = EvidenceIndex(records)
    results: list[ConstraintResult] = []
    for constraint_id in constraint_ids:
        answer = head_evidence.criterion_runner_at_head(
            index, criterion_id(constraint_id), revision
        )
        outcome: Outcome = UNVERIFIED
        if answer.run is not None:
            outcome = _run_outcome(answer.holds, answer.run)
        results.append(ConstraintResult(outcome, constraint_id, revision))
    return results
