from __future__ import annotations

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.execution_cost import new_dispatch_markers


class RedispatchError(ValueError):
    pass


def redispatch(project: Project, task: str, *, expected_revision: str) -> Record:
    records = [
        record
        for record in project.list("score:work-item")
        if record["subject"] == task and record["lifecycle_state"] != "superseded"
    ]
    if not records:
        raise RedispatchError(f"work-item {task!r} not found")
    item = max(records, key=lambda record: record["recorded_at"])
    if item["lifecycle_state"] != "in_progress":
        raise RedispatchError(f"task {task!r} must be in_progress to redispatch")
    payload = record_payload(item)
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
