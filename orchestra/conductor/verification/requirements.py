from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.types import Record
from orchestra.conductor.verification.evidence.head_evidence import EvidenceIndex, acceptance_latest
from orchestra.score.lookups import (
    LIVE_WORK_ITEM_STATES,
    current_phases,
    latest_record,
    record_order,
)
from orchestra.score.planning.acceptance import Acceptance, read_acceptance
from orchestra.score.planning.requirements import (
    requirements_in_body,
)
from orchestra.score.workflow.workflow_blockers import is_signed

RequirementState = Literal["verified", "failed", "unverified"]
VERIFIED: RequirementState = "verified"
UNVERIFIED: RequirementState = "unverified"

_WORK_ITEM = "score:work-item"
_SPECIFICATION = "score:specification"
_ACCEPTANCE = "score:acceptance"
_ASSESSMENT = "conductor:assessment"


@dataclass(frozen=True)
class RequirementStatus:
    requirement: str
    status: RequirementState
    acceptance_ids: tuple[str, ...] = ()
    check_run_ids: tuple[str, ...] = ()
    assessment_id: str | None = None
    assessed: str | None = None


def _text(record: Record, key: str) -> str | None:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) and value else None


def _phase_work_items(records: list[Record], phase: str) -> list[Record]:
    return [
        record
        for record in records
        if record["record_type"] == _WORK_ITEM
        and record["lifecycle_state"] in LIVE_WORK_ITEM_STATES
        and _text(record, "phase") == phase
    ]


def _phase_requirement_ids(records: list[Record], phase: str, current: Record | None) -> list[str]:
    specifications = [
        record
        for record in records
        if record["record_type"] == _SPECIFICATION
        and record["lifecycle_state"] == "active"
        and _text(record, "phase") == phase
    ]
    if current is not None and _text(current, "weight") == "light":
        return [requirement for requirement, _ in requirements_in_body(current.get("body", ""))]
    specification = latest_record(specifications)
    sources = [specification] if specification is not None else _phase_work_items(records, phase)
    requirements: list[str] = []
    for source in sources:
        values = record_payload(source).get("requirements")
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, str) and value not in requirements:
                requirements.append(value)
    return requirements


class RequirementIndex:
    """Requirement lookups for one unchanged record snapshot."""

    def __init__(self, records: list[Record]) -> None:
        self.by_id: dict[str, Record] = {}
        self.evidence = EvidenceIndex(records)
        self.phases = current_phases(records)
        self.sources: dict[str, list[Record]] = {
            slug: [phase] for slug, phase in self.phases.items()
        }
        self.acceptances: dict[tuple[str, str], list[Acceptance]] = {}
        self.assessments: dict[tuple[str, str], Record] = {}
        for record in records:
            self.by_id[record["id"]] = record
            record_type = record["record_type"]
            phase = _text(record, "phase")
            if record_type in (_SPECIFICATION, _WORK_ITEM) and phase is not None:
                self.sources.setdefault(phase, []).append(record)
            if record["lifecycle_state"] != "active" or phase is None:
                continue
            if record_type == _ACCEPTANCE:
                acceptance = read_acceptance(record)
                for requirement in dict.fromkeys(acceptance.requirements):
                    self.acceptances.setdefault((phase, requirement), []).append(acceptance)
            elif record_type == _ASSESSMENT:
                requirement = _text(record, "requirement")
                if requirement is not None:
                    key = (phase, requirement)
                    previous = self.assessments.get(key)
                    if previous is None or record_order(record) > record_order(previous):
                        self.assessments[key] = record


def _derive_requirement(
    index: RequirementIndex, phase: str, requirement: str, head: str | None
) -> RequirementStatus:
    acceptances = index.acceptances.get((phase, requirement), [])
    acceptance_ids = tuple(acceptance.id for acceptance in acceptances)
    latest_runs: list[Record] = []
    results: list[str] = []
    for acceptance in acceptances:
        run = acceptance_latest(index.evidence, acceptance.record, head).run
        if run is None:
            continue
        result = index.evidence.check_run(run).result
        if result == "pass" and acceptance.method == "manual" and not is_signed(run):
            continue
        latest_runs.append(run)
        results.append(result)
    status: RequirementState = "unverified"
    if "fail" in results:
        status = "failed"
    elif (
        acceptances
        and len(latest_runs) == len(acceptances)
        and all(result == "pass" for result in results)
    ):
        status = "verified"
    return RequirementStatus(
        requirement=requirement,
        status=status,
        acceptance_ids=acceptance_ids,
        check_run_ids=tuple(record["id"] for record in latest_runs),
    )


def _passes_after(derived: RequirementStatus, written: Record, by_id: dict[str, Record]) -> bool:
    if derived.status != "verified":
        return False
    return all(
        record_order(by_id[run_id]) > record_order(written) for run_id in derived.check_run_ids
    )


def requirement_status(
    records: list[Record],
    phase: str,
    head: str | None = None,
    *,
    index: RequirementIndex | None = None,
) -> dict[str, RequirementStatus]:
    if index is None:
        index = RequirementIndex(records)
    statuses: dict[str, RequirementStatus] = {}
    for requirement in _phase_requirement_ids(
        index.sources.get(phase, []), phase, index.phases.get(phase)
    ):
        derived = _derive_requirement(index, phase, requirement, head)
        written = index.assessments.get((phase, requirement))
        written_status = _text(written, "status") if written is not None else None
        if (
            written is not None
            and written_status not in (None, "verified")
            and not _passes_after(derived, written, index.by_id)
        ):
            derived = RequirementStatus(
                requirement=requirement,
                status="failed" if written_status == "failed" else "unverified",
                acceptance_ids=derived.acceptance_ids,
                check_run_ids=derived.check_run_ids,
                assessment_id=written["id"],
                assessed=written_status,
            )
        statuses[requirement] = derived
    return statuses


def is_verified(status: str) -> bool:
    return status == "verified"


def verified_requirements(statuses: dict[str, RequirementStatus]) -> frozenset[str]:
    return frozenset(
        requirement for requirement, status in statuses.items() if is_verified(status.status)
    )


def all_verified(statuses: dict[str, RequirementStatus]) -> bool:
    return bool(statuses) and all(is_verified(status.status) for status in statuses.values())


def release_ready(records: list[Record], phase: str, head: str | None = None) -> bool:
    return all_verified(requirement_status(records, phase, head))
