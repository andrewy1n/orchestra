from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.query import latest
from orchestra.canon.types import Record
from orchestra.conductor.head_evidence import EvidenceIndex, acceptance_latest
from orchestra.score.lookups import live_work_items
from orchestra.score.requirements import (
    acceptance_requirement_ids,
    phase_requirements,
    phase_weight,
)

RequirementState = Literal["verified", "failed", "unverified"]

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
    return live_work_items(phase, records)


def _phase_requirement_ids(records: list[Record], phase: str) -> list[str]:
    specifications = [
        record
        for record in records
        if record["record_type"] == _SPECIFICATION
        and record["lifecycle_state"] == "active"
        and _text(record, "phase") == phase
    ]
    if phase_weight(records, phase) == "light":
        return [requirement for requirement, _ in phase_requirements(records, phase)]
    specification = latest(specifications)
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


def _written_assessment(records: list[Record], phase: str, requirement: str) -> Record | None:
    return latest(
        [
            record
            for record in records
            if record["record_type"] == _ASSESSMENT
            and record["lifecycle_state"] == "active"
            and _text(record, "phase") == phase
            and _text(record, "requirement") == requirement
        ]
    )


def _derive_requirement(
    records: list[Record], index: EvidenceIndex, phase: str, requirement: str, head: str | None
) -> RequirementStatus:
    acceptances = [
        record
        for record in records
        if record["record_type"] == _ACCEPTANCE
        and record["lifecycle_state"] == "active"
        and _text(record, "phase") == phase
        and requirement in acceptance_requirement_ids(record)
    ]
    acceptance_ids = tuple(acceptance["id"] for acceptance in acceptances)
    latest_runs: list[Record] = []
    for acceptance in acceptances:
        run = acceptance_latest(index, acceptance, head).run
        if run is not None:
            latest_runs.append(run)
    results = [_text(record, "result") for record in latest_runs]
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
        by_id[run_id]["recorded_at"] > written["recorded_at"] for run_id in derived.check_run_ids
    )


def requirement_status(
    records: list[Record], phase: str, head: str | None = None
) -> dict[str, RequirementStatus]:
    by_id = {record["id"]: record for record in records}
    index = EvidenceIndex(records)
    statuses: dict[str, RequirementStatus] = {}
    for requirement in _phase_requirement_ids(records, phase):
        derived = _derive_requirement(records, index, phase, requirement, head)
        written = _written_assessment(records, phase, requirement)
        written_status = _text(written, "status") if written is not None else None
        if (
            written is not None
            and written_status not in (None, "verified")
            and not _passes_after(derived, written, by_id)
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
