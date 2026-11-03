"""Product areas with the ideas filed under them."""

from __future__ import annotations

from dataclasses import dataclass, field

from dashboard.backend.records import list_records, live_records, recorded_at, section
from dashboard.backend.snapshot import PLACEMENT_TYPE
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor.model_types import planning_payload as record_payload

AREA_TYPE = "composer:area"
IDEA_TYPE = "composer:idea"
SHOWN_STATUSES = ("open", "promoted")


@dataclass(frozen=True)
class AreaIdea:
    subject: str
    text: str
    status: str
    area: str
    effort: str
    phase: str


@dataclass(frozen=True)
class AreaView:
    subject: str
    title: str
    scope: str
    open_count: int
    ideas: list[AreaIdea] = field(default_factory=list)


def _home_area(idea: Record, placed: dict[str, str]) -> str:
    payload = record_payload(idea)
    if payload.get("status") == "promoted":
        home = placed.get(payload.get("effort") or "")
        if home:
            return home
    return payload.get("area") or ""


def _idea_text(idea: Record) -> str:
    for line in (idea.get("body") or "").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return idea.get("subject") or ""


def load_areas(target: Project) -> list[AreaView]:
    areas = live_records(list_records(target, AREA_TYPE))
    if not areas:
        return []
    ideas = [
        idea
        for idea in live_records(list_records(target, IDEA_TYPE))
        if record_payload(idea).get("status") in SHOWN_STATUSES
    ]
    ideas.sort(
        key=lambda idea: (
            record_payload(idea)["status"] != "open",  # pyright: ignore[reportTypedDictNotRequiredAccess]  # The shown-status filter establishes this field.
            recorded_at(idea),
            idea["subject"],
        )
    )
    placed = {
        record["subject"]: record_payload(record).get("area") or ""
        for record in live_records(list_records(target, PLACEMENT_TYPE))
    }
    views: list[AreaView] = []
    for area in sorted(areas, key=lambda record: record["subject"]):
        listed = [
            AreaIdea(
                subject=idea["subject"],
                text=_idea_text(idea),
                status=record_payload(idea)["status"],  # pyright: ignore[reportTypedDictNotRequiredAccess]  # The shown-status filter establishes this field.
                area=record_payload(idea).get("area") or "",
                effort=record_payload(idea).get("effort") or "",
                phase=record_payload(idea).get("phase") or "",
            )
            for idea in ideas
            if _home_area(idea, placed) == area["subject"]
        ]
        views.append(
            AreaView(
                subject=area["subject"],
                title=record_payload(area).get("title") or area["subject"],
                scope=section(area.get("body") or "", "Scope"),
                open_count=sum(idea.status == "open" for idea in listed),
                ideas=listed,
            )
        )
    return views
