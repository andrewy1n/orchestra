"""Derive requirement status, release readiness, phase progress and task assignment from records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
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
from orchestra.score.lookups import LIVE_WORK_ITEM_STATES, latest_record, live_work_items

WORK_ITEM = "score:work-item"
EFFORT = "score:effort"
PHASE = "score:phase"
ACCEPTANCE = "score:acceptance"
SPECIFICATION = "score:specification"
CHECK_RUN = "tuner:check-run"
ASSESSMENT = "conductor:assessment"
ASSIGNMENT = "conductor:assignment"
QUESTION = "score:continuity-question"


DORMANT_AFTER = timedelta(days=7)
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


def _goal(records: list[Record], effort: str) -> Record | None:
    return latest_record(
        [
            r
            for r in records
            if r["record_type"] == EFFORT
            and r["subject"] == effort
            and r["lifecycle_state"] != "superseded"
        ]
    )


def effort_autonomy(records: list[Record], effort: str) -> Autonomy:
    goal = _goal(records, effort)
    level = _text(goal, "autonomy") if goal is not None else None
    if level == "auto-plan":
        return "auto-plan"
    if level == "auto-phases":
        return "auto-phases"
    return "gated"


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _touch(stamps: dict[str, datetime], effort: str, record: Record) -> None:
    stamp = _parse_time(record["recorded_at"])
    current = stamps.get(effort)
    if current is None or stamp > current:
        stamps[effort] = stamp


def efforts_dormant(records: list[Record], now: datetime) -> dict[str, bool]:
    goals: dict[str, Record] = {}
    live: set[str] = set()
    blocking: set[str] = set()
    touched: dict[str, datetime] = {}
    for record in records:
        record_type = record["record_type"]
        if record_type == EFFORT and record["lifecycle_state"] != "superseded":
            subject = record["subject"]
            current = goals.get(subject)
            if current is None or (
                record.get("recorded_at") or "",
                record["id"],
            ) > (current.get("recorded_at") or "", current["id"]):
                goals[subject] = record
        elif (
            record_type == PHASE
            and record["lifecycle_state"] in ("planned", "in_progress")
            and (effort_name := _text(record, "effort")) is not None
        ):
            live.add(effort_name)
        elif (
            record_type == QUESTION
            and record["lifecycle_state"] == "open"
            and record_payload(record).get("blocking") is True
        ):
            blocking.add(record["subject"])
        effort_name = _text(record, "effort")
        if effort_name is not None:
            _touch(touched, effort_name, record)
        if record_type in (EFFORT, QUESTION):
            _touch(touched, record["subject"], record)
    dormant: dict[str, bool] = {}
    for effort, goal in goals.items():
        if _text(goal, "status") == "closed" or effort in live or effort in blocking:
            dormant[effort] = False
            continue
        stamp = touched.get(effort)
        dormant[effort] = stamp is not None and now - stamp >= DORMANT_AFTER
    return dormant


def effort_dormant(records: list[Record], effort: str, now: datetime) -> bool:
    return efforts_dormant(records, now).get(effort, False)
