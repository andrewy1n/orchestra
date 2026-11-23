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


@dataclass(frozen=True)
class FailedAttempt:
    attempted_action: str
    retry_when: str


def failed_attempt(record: Record) -> FailedAttempt:
    payload = record_payload(record)
    action = payload.get("attempted_action")
    retry = payload.get("retry_when")
    return FailedAttempt(
        attempted_action=action if isinstance(action, str) else "",
        retry_when=retry if isinstance(retry, str) else "",
    )


def referenced_work_item(record: Record) -> str | None:
    return _text(record, "work_item")


def referenced_assignment(record: Record) -> str | None:
    return _text(record, "assignment")


def assignments_of(work_item: Record, records: list[Record]) -> list[Record]:
    names = {work_item["id"], work_item["subject"]}
    return [r for r in records if referenced_work_item(r) in names]


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
