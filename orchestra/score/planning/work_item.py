from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import JsonValue, Record
from orchestra.score.lookups import current_version


class WorkItemShapeError(ValueError):
    def __init__(self, record_id: str, field: str, expected: str) -> None:
        super().__init__(f"work-item {record_id}: field {field!r} must be {expected}")
        self.record_id = record_id
        self.field = field


@dataclass(frozen=True)
class WorkItem:
    id: str
    subject: str
    lifecycle_state: str
    phase: str
    effort: str
    write_root: str
    requirements: tuple[str, ...]
    record: Record


def read_work_item(record: Record) -> WorkItem:
    payload = record_payload(record)
    record_id = record["id"]
    return WorkItem(
        id=record_id,
        subject=record["subject"],
        lifecycle_state=record["lifecycle_state"],
        phase=_text(record_id, "phase", payload.get("phase")),
        effort=_text(record_id, "effort", payload.get("effort")),
        write_root=_text(record_id, "write_root", payload.get("write_root", "")),
        requirements=_strings(record_id, "requirements", payload.get("requirements", [])),
        record=record,
    )


def current_work_item(subject: str, records: Sequence[Record]) -> WorkItem | None:
    found = current_version("score:work-item", subject, records)
    return None if found is None else read_work_item(found)


def _text(record_id: str, field: str, value: JsonValue | None) -> str:
    if not isinstance(value, str):
        raise WorkItemShapeError(record_id, field, "a string")
    return value


def _strings(record_id: str, field: str, value: JsonValue | None) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise WorkItemShapeError(record_id, field, "a list of strings")
    strings = tuple(entry for entry in value if isinstance(entry, str))
    if len(strings) != len(value):
        raise WorkItemShapeError(record_id, field, "a list of strings")
    return strings
