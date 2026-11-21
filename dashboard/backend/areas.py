"""Product areas with the ideas filed under them."""

from __future__ import annotations

from dataclasses import dataclass, field

from dashboard.backend.records import list_records, live_records, recorded_at
from orchestra.canon.project import Project
from orchestra.composer.records import (
    AREA,
    IDEA,
    PLACEMENT,
    current_placements,
    home_area,
    read_area,
    read_idea,
)

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
    areas = [read_area(record) for record in live_records(list_records(target, AREA))]
    if not areas:
        return []
    ideas = sorted(
        (
            (recorded_at(record), idea)
            for record in live_records(list_records(target, IDEA))
            if (idea := read_idea(record)).status in SHOWN_STATUSES
        ),
        key=lambda entry: (entry[1].status != "open", entry[0], entry[1].subject),
    )
    placed = current_placements(live_records(list_records(target, PLACEMENT)))
    views: list[AreaView] = []
    for area in sorted(areas, key=lambda area: area.subject):
        listed = [
            AreaIdea(
                subject=idea.subject,
                text=idea.text,
                status=idea.status,
                area=idea.area,
                effort=idea.effort,
                phase=idea.phase,
            )
            for _, idea in ideas
            if home_area(idea, placed) == area.subject
        ]
        views.append(
            AreaView(
                subject=area.subject,
                title=area.title,
                scope=area.scope,
                open_count=sum(idea.status == "open" for idea in listed),
                ideas=listed,
            )
        )
    return views
