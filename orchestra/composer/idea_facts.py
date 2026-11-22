from __future__ import annotations

from orchestra.canon import record_payload
from orchestra.canon.types import Record
from orchestra.composer.records import AREA, IDEA

IDEA_TYPE = IDEA
AREA_TYPE = AREA


def idea_status(record: Record) -> str | None:
    value = record_payload(record).get("status")
    return value if isinstance(value, str) else None


def is_open_backlog_idea(record: Record) -> bool:
    return idea_status(record) == "open" and bool(record_payload(record).get("effort"))


def is_roadmap_idea(record: Record) -> bool:
    return idea_status(record) in ("open", "promoted")
