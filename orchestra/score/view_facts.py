from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import JsonValue, Record
from orchestra.score.workspace_facts import CONSTRAINT_TYPE, POSITION_TYPE

EFFORT_TYPE = "score:effort"
RUN_TYPE = "score:run"


@dataclass(frozen=True)
class ConstraintLine:
    subject: str
    statement: str


def _text(value: JsonValue | None) -> str:
    return value if isinstance(value, str) else ""


def effort_of(record: Record) -> str | None:
    if record.get("record_type") == EFFORT_TYPE:
        return record.get("subject")
    value = record_payload(record).get("effort")
    return value if isinstance(value, str) and value else None


def is_closed(record: Record) -> bool:
    return record_payload(record).get("status") == "closed"


def in_effort(record: Record, effort: str | None) -> bool:
    if effort is None:
        return True
    own = effort_of(record)
    if own is not None:
        return own == effort
    return record_payload(record).get("scope") == effort


def effort_position_stamps(records: Sequence[Record]) -> dict[str, str]:
    stamps: dict[str, str] = {}
    for record in records:
        if (
            record["record_type"] != POSITION_TYPE
            or record.get("lifecycle_state") != "active"
            or is_closed(record)
        ):
            continue
        effort = effort_of(record)
        stamp = record.get("recorded_at")
        if effort and stamp and record_payload(record).get("scope") == "effort":
            stamps[effort] = max(stamp, stamps.get(effort, ""))
    return stamps


def effort_constraint_lines(
    records: Sequence[Record], efforts: Collection[str]
) -> list[ConstraintLine]:
    matches = sorted(
        (
            record
            for record in records
            if record["record_type"] == CONSTRAINT_TYPE
            and record.get("lifecycle_state") == "active"
            and record_payload(record).get("effort") in efforts
        ),
        key=lambda record: record.get("subject") or "",
    )
    return [
        ConstraintLine(
            subject=str(record.get("subject")),
            statement=_text(record_payload(record).get("statement")),
        )
        for record in matches
    ]
