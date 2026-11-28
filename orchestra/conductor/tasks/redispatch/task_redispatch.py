from __future__ import annotations

import re

from orchestra.canon import record_payload
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.canon.validation import ValidationError
from orchestra.conductor.tasks.execution_cost import new_dispatch_markers
from orchestra.conductor.tasks.redispatch.failure_key import failure_key
from orchestra.score.lookups import (
    current_phase,
    live_work_items,
    owning_work_item,
    record_order,
)
from orchestra.score.workflow.workflow_blockers import (
    WorkflowBlockerError,
    blocked_tasks,
    phase_blockers,
)
from orchestra.tuner.evidence.record_facts import (
    RecordShapeError,
    check_run_facts,
    check_run_failing_nodes,
)

DEFAULT_MAX_REDISPATCHES = 2
ATTEMPT_EVENT = "conductor:redispatch-attempt"
_BUDGET_LINE = re.compile(r"^retry_max_redispatches:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
_RUN_FACTS = re.compile(r"^## Run facts\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)


class RedispatchError(ValueError):
    pass


def _max_redispatches(records: list[Record], phase: str) -> int:
    record = current_phase(phase, records) if phase else None
    facts = _RUN_FACTS.search(record.get("body") or "") if record else None
    found = _BUDGET_LINE.search(facts.group(1)) if facts else None
    if found is None:
        return DEFAULT_MAX_REDISPATCHES
    value = found.group(1)
    if not value.isdigit():
        raise RedispatchError(f"retry_max_redispatches must be a whole number, got {value!r}")
    return int(value)


def latest_failure_key(records: list[Record], task: str) -> str | None:
    items = [
        record
        for record in records
        if record["record_type"] == "score:work-item" and record["lifecycle_state"] != "superseded"
    ]
    failing: list[Record] = []
    for record in records:
        if record["record_type"] != "tuner:check-run":
            continue
        owner = owning_work_item(record["subject"], items)
        if owner is None or owner["subject"] != task:
            continue
        try:
            if check_run_facts(record).result == "fail":
                failing.append(record)
        except RecordShapeError as exc:
            raise RedispatchError(str(exc)) from exc
    if not failing:
        return None
    latest = max(failing, key=record_order)
    try:
        nodes = check_run_failing_nodes(latest)
        return failure_key(check_run_facts(latest).criterion_id, list(nodes))
    except RecordShapeError as exc:
        raise RedispatchError(str(exc)) from exc


def _used(records: list[Record], task: str, key: str) -> int:
    return sum(
        1
        for record in records
        if record["record_type"] == ATTEMPT_EVENT
        and record_payload(record).get("work_item") == task
        and record_payload(record).get("failure_key") == key
    )


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
    phase = payload.get("phase") or ""
    if not isinstance(phase, str):
        raise RedispatchError(f"task {task!r} has an invalid phase")
    if phase:
        try:
            blockers = phase_blockers(records, phase)
        except WorkflowBlockerError as exc:
            raise RedispatchError(str(exc)) from exc
        if task in blocked_tasks(live_work_items(phase, records), blockers):
            raise RedispatchError(f"task {task!r} is blocked by a human decision")
    attempts = payload.get("attempts", 0)
    if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts < 0:
        raise RedispatchError(f"task {task!r} has invalid attempts")
    budget = _max_redispatches(records, phase)
    key = latest_failure_key(records, task)
    if key is None and attempts >= budget:
        raise RedispatchError(
            f"task {task!r} used its re-dispatch budget of {budget} with no failing check-run"
        )
    if key is not None and _used(records, task, key) >= budget:
        raise RedispatchError(f"task {task!r} used its re-dispatch budget for failure {key}")
    markers = new_dispatch_markers()
    updates: JsonObject = {
        "attempts": attempts + 1,
        "dispatch_id": markers.dispatch_id,
        "dispatch_started_at": markers.dispatch_started_at,
    }
    updated = project.update(
        item["id"],
        record_type="score:work-item",
        payload=updates,
        expected_revision=expected_revision,
    )
    if key is not None:
        event: JsonObject = {
            "work_item": task,
            "failure_key": key,
            "dispatch_id": markers.dispatch_id,
        }
        effort = payload.get("effort")
        if isinstance(effort, str) and effort:
            event["effort"] = effort
        try:
            project.create(record_type=ATTEMPT_EVENT, subject=task, payload=event, body="")
        except (StoreError, ValidationError) as exc:
            raise RedispatchError(
                f"task {task!r} was re-dispatched but its attempt event failed: {exc}"
            ) from exc
    return updated
