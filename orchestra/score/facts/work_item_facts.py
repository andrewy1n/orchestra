from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import JsonValue, Record
from orchestra.score.lookups import LIVE_WORK_ITEM_STATES, owning_work_item
from orchestra.score.planning.executor import ExecutorTask


@dataclass(frozen=True)
class RecordScope:
    effort: str | None
    phase: str | None


@dataclass(frozen=True)
class WorkItemFacts:
    scope: RecordScope
    requirements: tuple[str, ...]
    decisions: tuple[str, ...]
    assignee: str | None
    write_root: str | None


def _text(value: JsonValue | None) -> str | None:
    return value if isinstance(value, str) and value else None


def _strings(value: JsonValue | None) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def record_scope(record: Record) -> RecordScope:
    payload = record_payload(record)
    effort = payload.get("effort")
    phase = payload.get("phase")
    return RecordScope(
        effort=effort if isinstance(effort, str) else None,
        phase=phase if isinstance(phase, str) else None,
    )


def work_item_facts(record: Record) -> WorkItemFacts:
    payload = record_payload(record)
    return WorkItemFacts(
        scope=record_scope(record),
        requirements=_strings(payload.get("requirements")),
        decisions=_strings(payload.get("decisions")),
        assignee=_text(payload.get("assignee")),
        write_root=_text(payload.get("write_root")),
    )


def executor_task(record: Record) -> ExecutorTask:
    payload = record_payload(record)
    estimate = payload.get("estimate_minutes")
    size = payload.get("size")
    executor = payload.get("executor")
    assignee = payload.get("assignee")
    return ExecutorTask(
        subject=record["subject"],
        size=size if isinstance(size, str) and size else None,
        estimate_minutes=estimate if type(estimate) is int else None,
        executor=executor if isinstance(executor, str) else None,
        assignee=assignee if isinstance(assignee, str) else None,
    )


@dataclass(frozen=True)
class TaskPlan:
    title: str
    phase: str
    size: str
    estimate_minutes: int | None
    attempts: int


def task_plan(record: Record) -> TaskPlan:
    payload = record_payload(record)
    title = payload.get("title")
    phase = payload.get("phase")
    size = payload.get("size")
    estimate = payload.get("estimate_minutes")
    attempts = payload.get("attempts")
    return TaskPlan(
        title=title if isinstance(title, str) else "",
        phase=phase if isinstance(phase, str) else "",
        size=size if isinstance(size, str) else "",
        estimate_minutes=estimate if type(estimate) is int else None,
        attempts=attempts if type(attempts) is int else 0,
    )


def work_item_status(record: Record) -> str | None:
    state = record["lifecycle_state"]
    if state == "planned":
        return "ready" if (record.get("derived") or {}).get("ready") else "waiting"
    return {"in_progress": "running", "done": "done", "withdrawn": "withdrawn"}.get(state)


def decision_choice(record: Record) -> JsonValue | None:
    return record_payload(record).get("choice")


def tasks_by_requirement(tasks: Sequence[Record], phase: str) -> dict[str, list[Record]]:
    grouped: dict[str, list[Record]] = {}
    for task in tasks:
        if task["lifecycle_state"] == "superseded":
            continue
        facts = work_item_facts(task)
        if facts.scope.phase != phase:
            continue
        for requirement in dict.fromkeys(facts.requirements):
            grouped.setdefault(requirement, []).append(task)
    return grouped


def owning_task_id(subject: str, tasks: Sequence[Record]) -> str:
    live = [task for task in tasks if task["lifecycle_state"] in LIVE_WORK_ITEM_STATES]
    owner = owning_work_item(subject, live)
    return owner["id"] if owner else ""
