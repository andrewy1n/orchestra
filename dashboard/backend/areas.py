"""Product areas with the ideas filed under them."""

from __future__ import annotations

from orchestra.canon import record_payload
from dataclasses import dataclass, field

from orchestra.canon.project import Project
from dashboard.backend.records import _list, _live, _recorded_at, _section
from dashboard.backend.snapshot import PLACEMENT_TYPE, _backlog_text

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


def _home_area(idea: dict, placed: dict[str, str]) -> str:
    payload = record_payload(idea)
    if payload.get("status") == "promoted":
        home = placed.get(payload.get("effort") or "")
        if home:
            return home
    return payload.get("area") or ""


def load_areas(target: Project) -> list[AreaView]:
    areas = _live(_list(target, AREA_TYPE))
    if not areas:
        return []
    ideas = [
        idea for idea in _live(_list(target, IDEA_TYPE))
        if record_payload(idea).get("status") in SHOWN_STATUSES
    ]
    ideas.sort(key=lambda idea: (record_payload(idea)["status"] != "open", _recorded_at(idea), idea["subject"]))
    placed = {
        record["subject"]: record_payload(record).get("area") or ""
        for record in _live(_list(target, PLACEMENT_TYPE))
    }
    views = []
    for area in sorted(areas, key=lambda record: record["subject"]):
        listed = [
            AreaIdea(
                subject=idea["subject"],
                text=_backlog_text(idea),
                status=record_payload(idea)["status"],
                area=record_payload(idea).get("area") or "",
                effort=record_payload(idea).get("effort") or "",
                phase=record_payload(idea).get("phase") or "",
            )
            for idea in ideas
            if _home_area(idea, placed) == area["subject"]
        ]
        views.append(AreaView(
            subject=area["subject"],
            title=record_payload(area).get("title") or area["subject"],
            scope=_section(area.get("body") or "", "Scope"),
            open_count=sum(idea.status == "open" for idea in listed),
            ideas=listed,
        ))
    return views
