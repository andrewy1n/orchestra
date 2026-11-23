from __future__ import annotations

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.tasks.execution_cost import new_dispatch_markers
from orchestra.score.lookups import live_work_items, record_order
from orchestra.score.workflow.workflow_blockers import (
    WorkflowBlockerError,
    blocked_tasks,
    phase_blockers,
)


class RedispatchError(ValueError):
    pass


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
    markers = new_dispatch_markers()
    updates: JsonObject = {
        "attempts": attempts + 1,
        "dispatch_id": markers.dispatch_id,
        "dispatch_started_at": markers.dispatch_started_at,
    }
    return project.update(
        item["id"],
        record_type="score:work-item",
        payload=updates,
        expected_revision=expected_revision,
    )
