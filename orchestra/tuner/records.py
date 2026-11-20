from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.fields import optional_bool, optional_text, optional_text_list, required_text
from orchestra.canon.types import JsonObject, Record

CheckResult = Literal["pass", "fail", "blocked", "insufficient"]


@dataclass(frozen=True)
class CheckRun:
    id: str
    criterion_id: str
    result: CheckResult
    revision: str
    signed_by: str
    recorded_at: str
    write_order: int
    record: Record


@dataclass(frozen=True)
class Finding:
    id: str
    claim: str
    basis: str
    invalidated_when: str
    effort: str
    needs: str
    phase: str | None
    resolution_note: str | None
    severity: str | None
    contradicted_by: tuple[str, ...]
    record: Record


@dataclass(frozen=True)
class EvidenceBinding:
    id: str
    observation_id: str
    claim_id: str
    base_rev: str
    head_rev: str
    effort: str | None
    retired: bool
    record: Record


def _result(record: Record, payload: JsonObject) -> CheckResult:
    value = required_text(record, payload, "result")
    if value == "pass" or value == "fail" or value == "blocked" or value == "insufficient":
        return value
    raise RecordShapeError(record["id"], "result", "must be pass, fail, blocked or insufficient")


def read_check_run(record: Record, write_order: int) -> CheckRun:
    payload = record_payload(record)
    return CheckRun(
        id=record["id"],
        criterion_id=required_text(record, payload, "criterion_id"),
        result=_result(record, payload),
        revision=required_text(record, payload, "revision"),
        signed_by=required_text(record, payload, "signed_by"),
        recorded_at=record["recorded_at"],
        write_order=write_order,
        record=record,
    )


def read_finding(record: Record) -> Finding:
    payload = record_payload(record)
    return Finding(
        id=record["id"],
        claim=required_text(record, payload, "claim"),
        basis=required_text(record, payload, "basis"),
        invalidated_when=required_text(record, payload, "invalidated_when"),
        effort=required_text(record, payload, "effort"),
        needs=required_text(record, payload, "needs"),
        phase=optional_text(record, payload, "phase"),
        resolution_note=optional_text(record, payload, "resolution_note"),
        severity=optional_text(record, payload, "severity"),
        contradicted_by=optional_text_list(record, payload, "contradicted_by"),
        record=record,
    )


def read_evidence_binding(record: Record) -> EvidenceBinding:
    payload = record_payload(record)
    return EvidenceBinding(
        id=record["id"],
        observation_id=required_text(record, payload, "observation_id"),
        claim_id=required_text(record, payload, "claim_id"),
        base_rev=required_text(record, payload, "base_rev"),
        head_rev=required_text(record, payload, "head_rev"),
        effort=optional_text(record, payload, "effort"),
        retired=optional_bool(record, payload, "retired") is True,
        record=record,
    )
