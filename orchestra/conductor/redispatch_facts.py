from __future__ import annotations

from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import JsonValue, Record


@dataclass(frozen=True)
class RedispatchFacts:
    task: str
    revision: str
    attempts: JsonValue
    dispatch_id: JsonValue
    dispatch_started_at: JsonValue
    assignee: JsonValue
    write_root: JsonValue


def redispatch_facts(record: Record) -> RedispatchFacts:
    payload = record_payload(record)
    return RedispatchFacts(
        task=record["subject"],
        revision=record["revision"],
        attempts=payload.get("attempts"),
        dispatch_id=payload.get("dispatch_id"),
        dispatch_started_at=payload.get("dispatch_started_at"),
        assignee=payload.get("assignee"),
        write_root=payload.get("write_root"),
    )
