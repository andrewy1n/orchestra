from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.query import latest
from orchestra.canon.types import JsonValue, Record


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
    return WorkItem(
        id=record["id"],
        subject=record["subject"],
        lifecycle_state=record["lifecycle_state"],
        phase=_text(payload.get("phase")),
        effort=_text(payload.get("effort")),
        write_root=_text(payload.get("write_root")),
        requirements=_strings(payload.get("requirements")),
        record=record,
    )


def current_work_item(subject: str, records: Sequence[Record]) -> WorkItem | None:
    corrected = {
        target
        for record in records
        for target in (record.get("relationships") or {}).get("corrects") or []
    }
    found = latest(
        record
        for record in records
        if record["record_type"] == "score:work-item"
        and record["subject"] == subject
        and record["lifecycle_state"] != "superseded"
        and record["id"] not in corrected
    )
    return None if found is None else read_work_item(found)


def _text(value: JsonValue | None) -> str:
    return value if isinstance(value, str) else ""


def _strings(value: JsonValue | None) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(entry for entry in value if isinstance(entry, str))
