"""Place an effort in a product area."""

from __future__ import annotations

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.canon.validation import ValidationError
from orchestra.composer.records import current_area
from orchestra.score.planning.effort import current_effort

PLACEMENT = "composer:placement"


class PlacementError(Exception):
    pass


def place(project: Project, effort: str, area: str) -> Record:
    records = project.records()
    if current_effort(records, effort) is None:
        raise PlacementError(f"score:effort {effort!r} does not exist")
    if current_area(records, area) is None:
        raise PlacementError(f"composer:area {area!r} does not exist")
    payload: JsonObject = {"area": area}
    try:
        try:
            current = project.resolve(PLACEMENT, effort)
        except StoreError:
            return project.create(record_type=PLACEMENT, subject=effort, payload=payload)
        if current.get("lifecycle_state") != "active":
            return project.create(record_type=PLACEMENT, subject=effort, payload=payload)
        if current["payload"].get("area") == area:
            return current
        return project.supersede(current["id"], payload=payload)["record"]
    except (StoreError, ValidationError) as exc:
        raise PlacementError(str(exc)) from exc
