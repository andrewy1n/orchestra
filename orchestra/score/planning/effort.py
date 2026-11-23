from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.fields import optional_text, required_text
from orchestra.canon.types import Record
from orchestra.score.lookups import latest_record

EFFORT = "score:effort"


@dataclass(frozen=True)
class Effort:
    id: str
    subject: str
    goal: str
    kind: str
    status: Literal["open", "closed"] | None
    autonomy: Literal["gated", "auto-plan", "auto-phases"] | None
    record: Record


@dataclass(frozen=True)
class EffortScanFinding:
    record_id: str
    record_type: str
    field: str
    message: str


def read_effort(record: Record) -> Effort:
    payload = record_payload(record)
    goal = required_text(record, payload, "goal")
    kind = required_text(record, payload, "kind")
    status = optional_text(record, payload, "status")
    autonomy = optional_text(record, payload, "autonomy")
    if status is not None and status != "open" and status != "closed":
        raise RecordShapeError(record["id"], "status", "must be open or closed")
    if (
        autonomy is not None
        and autonomy != "gated"
        and autonomy != "auto-plan"
        and autonomy != "auto-phases"
    ):
        raise RecordShapeError(record["id"], "autonomy", "must be gated, auto-plan or auto-phases")
    return Effort(
        id=record["id"],
        subject=record["subject"],
        goal=goal,
        kind=kind,
        status=status,
        autonomy=autonomy,
        record=record,
    )


def record_effort(record: Record) -> str | None:
    effort = record_payload(record).get("effort")
    return effort if isinstance(effort, str) else None


def _live_efforts(records: Sequence[Record]) -> list[Record]:
    return [
        record
        for record in records
        if record["record_type"] == EFFORT and record["lifecycle_state"] != "superseded"
    ]


def current_effort(records: Sequence[Record], subject: str) -> Effort | None:
    record = latest_record(r for r in _live_efforts(records) if r["subject"] == subject)
    return read_effort(record) if record is not None else None


def current_efforts(records: Sequence[Record]) -> dict[str, Effort]:
    grouped: dict[str, list[Record]] = {}
    for record in _live_efforts(records):
        grouped.setdefault(record["subject"], []).append(record)
    result: dict[str, Effort] = {}
    for subject in sorted(grouped):
        latest = latest_record(grouped[subject])
        if latest is not None:
            result[subject] = read_effort(latest)
    return result


def scan_effort_records(records: Sequence[Record]) -> list[EffortScanFinding]:
    findings: list[EffortScanFinding] = []
    for record in _live_efforts(records):
        try:
            read_effort(record)
        except RecordShapeError as error:
            findings.append(
                EffortScanFinding(
                    error.record_id, record["record_type"], error.field, error.message
                )
            )
    return findings
