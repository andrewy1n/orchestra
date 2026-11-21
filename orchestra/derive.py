"""Derive requirement status, release readiness, phase progress and task assignment from records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.types import Record
from orchestra.conductor.requirements import (
    RequirementState as RequirementState,
)
from orchestra.conductor.requirements import (
    RequirementStatus as RequirementStatus,
)
from orchestra.conductor.requirements import (
    all_verified,
    requirement_status,
)
from orchestra.score.effort import current_effort
from orchestra.score.lookups import LIVE_WORK_ITEM_STATES, latest_record, live_work_items

WORK_ITEM = "score:work-item"
ACCEPTANCE = "score:acceptance"
SPECIFICATION = "score:specification"
CHECK_RUN = "tuner:check-run"
ASSESSMENT = "conductor:assessment"
ASSIGNMENT = "conductor:assignment"


Autonomy = Literal["gated", "auto-plan", "auto-phases"]


@dataclass(frozen=True)
class PhaseProgress:
    counts: dict[str, int] = field(default_factory=dict[str, int])
    done: int = 0
    total: int = 0
    in_progress: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskAssignment:
    assignee: str | None
    write_root: str | None


def _text(record: Record, key: str) -> str | None:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) and value else None


def release_ready(records: list[Record], phase: str, head: str | None = None) -> bool:
    return all_verified(requirement_status(records, phase, head))


def phase_progress(records: list[Record], phase: str) -> PhaseProgress:
    items = live_work_items(phase, records)
    counts = {state: 0 for state in LIVE_WORK_ITEM_STATES}
    for item in items:
        counts[item["lifecycle_state"]] += 1
    return PhaseProgress(
        counts=counts,
        done=counts["done"],
        total=len(items),
        in_progress=tuple(i["subject"] for i in items if i["lifecycle_state"] == "in_progress"),
    )


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


def effort_autonomy(records: list[Record], effort: str) -> Autonomy:
    current = current_effort(records, effort)
    level = current.autonomy if current is not None else None
    return level or "gated"
