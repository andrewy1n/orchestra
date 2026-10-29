"""Product areas with the ideas filed under them."""

from __future__ import annotations

from dataclasses import dataclass, field

from orchestra.canon.project import Project
from dashboard.backend.records import _list, _live, _payload, _recorded_at, _section
from dashboard.backend.snapshot import _backlog_text

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


def load_areas(target: Project) -> list[AreaView]:
    areas = _live(_list(target, AREA_TYPE))
    if not areas:
        return []
    ideas = [
        idea for idea in _live(_list(target, IDEA_TYPE))
        if _payload(idea).get("status") in SHOWN_STATUSES
    ]
    ideas.sort(key=lambda idea: (_payload(idea)["status"] != "open", _recorded_at(idea), idea["subject"]))
    views = []
    for area in sorted(areas, key=lambda record: record["subject"]):
        listed = [
            AreaIdea(
                subject=idea["subject"],
                text=_backlog_text(idea),
                status=_payload(idea)["status"],
                area=area["subject"],
                effort=_payload(idea).get("effort") or "",
                phase=_payload(idea).get("phase") or "",
            )
            for idea in ideas
            if _payload(idea).get("area") == area["subject"]
        ]
        views.append(AreaView(
            subject=area["subject"],
            title=_payload(area).get("title") or area["subject"],
            scope=_section(area.get("body") or "", "Scope"),
            open_count=sum(idea.status == "open" for idea in listed),
            ideas=listed,
        ))
    return views
