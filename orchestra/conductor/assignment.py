from __future__ import annotations

from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import Record
from orchestra.score.lookups import latest_record

ASSIGNMENT = "conductor:assignment"


@dataclass(frozen=True)
class TaskAssignment:
    assignee: str | None
    write_root: str | None


def _text(record: Record, key: str) -> str | None:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) and value else None


def task_assignment(work_item: Record, records: list[Record]) -> TaskAssignment | None:
    assignee = _text(work_item, "assignee")
    write_root = _text(work_item, "write_root")
    if assignee is None or write_root is None:
        names = {work_item["id"], work_item["subject"]}
        written = latest_record(
            [
                r
                for r in records
                if r["record_type"] == ASSIGNMENT and _text(r, "work_item") in names
            ]
        )
        if written is not None:
            assignee = assignee or _text(written, "assignee") or _text(written, "executor")
            write_root = write_root or _text(written, "write_root")
    if assignee is None and write_root is None:
        return None
    return TaskAssignment(assignee=assignee, write_root=write_root)
