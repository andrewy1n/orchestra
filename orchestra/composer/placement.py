"""Place an effort in a product area."""

from __future__ import annotations

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.canon.validation import ValidationError

PLACEMENT = "composer:placement"


class PlacementError(Exception):
    pass


def _require(project: Project, record_type: str, subject: str) -> None:
    try:
        project.resolve(record_type, subject)
    except StoreError as exc:
        raise PlacementError(f"{record_type} {subject!r} does not exist") from exc


def place(project: Project, effort: str, area: str) -> Record:
    _require(project, "score:effort", effort)
    _require(project, "composer:area", area)
    payload: JsonObject = {"area": area}
    try:
        try:
            current = project.resolve(PLACEMENT, effort)
        except StoreError:
            return project.create(record_type=PLACEMENT, subject=effort, payload=payload)
        if current.get("lifecycle_state") != "active":
            return project.create(record_type=PLACEMENT, subject=effort, payload=payload)
        return project.supersede(current["id"], payload=payload)["record"]
    except (StoreError, ValidationError) as exc:
        raise PlacementError(str(exc)) from exc
