from __future__ import annotations

from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import JsonValue, Record
from orchestra.score.executor import ExecutorTask


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


def decision_choice(record: Record) -> JsonValue | None:
    return record_payload(record).get("choice")
