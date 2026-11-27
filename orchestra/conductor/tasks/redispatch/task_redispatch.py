from __future__ import annotations

import re

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.tasks.execution_cost import new_dispatch_markers
from orchestra.conductor.tasks.redispatch.failure_key import failure_key
from orchestra.score.lookups import live_work_items, record_order
from orchestra.score.workflow.workflow_blockers import (
    WorkflowBlockerError,
    blocked_tasks,
    phase_blockers,
)

DEFAULT_MAX_REDISPATCHES = 2
_BUDGET_LINE = re.compile(r"^retry_max_redispatches:\s*(\d+)\s*$", re.MULTILINE)
_RUN_FACTS = re.compile(r"^## Run facts\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)


class RedispatchError(ValueError):
    pass


def _max_redispatches(records: list[Record], phase: object) -> int:
    for record in records:
        if (
            record["record_type"] == "score:phase"
            and record["subject"] == phase
            and record["lifecycle_state"] != "superseded"
        ):
            facts = _RUN_FACTS.search(record.get("body") or "")
            found = _BUDGET_LINE.search(facts.group(1)) if facts else None
            if found:
                return int(found.group(1))
    return DEFAULT_MAX_REDISPATCHES


def latest_failure_key(records: list[Record], task: str) -> str | None:
    failing = [
        record
        for record in records
        if record["record_type"] == "tuner:check-run"
        and record["subject"] == task
        and record_payload(record).get("result") == "fail"
    ]
    if not failing:
        return None
    payload = record_payload(max(failing, key=record_order))
    criterion = payload.get("criterion_id")
    nodes = payload.get("failing_node_ids")
    node_ids = [n for n in nodes if isinstance(n, str)] if isinstance(nodes, list) else []
    return failure_key(criterion if isinstance(criterion, str) else "", node_ids)


def redispatch(project: Project, task: str, *, expected_revision: str) -> Record:
    records = project.records()
    candidates = [
        record
        for record in records
        if record["record_type"] == "score:work-item"
        and record["subject"] == task
        and record["lifecycle_state"] != "superseded"
    ]
    if not candidates:
        raise RedispatchError(f"work-item {task!r} not found")
    item = max(candidates, key=record_order)
    if item["lifecycle_state"] != "in_progress":
        raise RedispatchError(f"task {task!r} must be in_progress to redispatch")
    payload = record_payload(item)
    phase = payload.get("phase")
    if isinstance(phase, str) and phase:
        try:
            blockers = phase_blockers(records, phase)
        except WorkflowBlockerError as exc:
            raise RedispatchError(str(exc)) from exc
        if task in blocked_tasks(live_work_items(phase, records), blockers):
            raise RedispatchError(f"task {task!r} is blocked by a human decision")
    attempts = payload.get("attempts", 0)
    if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 0:
        raise RedispatchError(f"task {task!r} has invalid attempts")
    updates: JsonObject = {"attempts": attempts + 1}
    key = latest_failure_key(records, task)
    if key is not None:
        counts = payload.get("failure_attempts")
        failure_attempts: JsonObject = dict(counts) if isinstance(counts, dict) else {}
        used = failure_attempts.get(key, 0)
        if not isinstance(used, int) or isinstance(used, bool) or used < 0:
            raise RedispatchError(f"task {task!r} has invalid failure_attempts")
        if used >= _max_redispatches(records, phase):
            raise RedispatchError(f"task {task!r} used its re-dispatch budget for failure {key}")
        failure_attempts[key] = used + 1
        updates["failure_attempts"] = failure_attempts
    markers = new_dispatch_markers()
    updates["dispatch_id"] = markers.dispatch_id
    updates["dispatch_started_at"] = markers.dispatch_started_at
    return project.update(
        item["id"],
        record_type="score:work-item",
        payload=updates,
        expected_revision=expected_revision,
    )
