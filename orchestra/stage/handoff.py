from __future__ import annotations

from collections.abc import Collection, Mapping

from orchestra.canon.types import Record
from orchestra.conductor.phases.progress.phase_progress import PhaseProgress
from orchestra.score.facts.view_facts import (
    ConstraintLine,
    effort_constraint_lines,
    effort_position_stamps,
)
from orchestra.views import render as views


def hook_handoff_sections(
    records: list[Record],
    dormant: Collection[str] = (),
    progress: Mapping[str, PhaseProgress] | None = None,
) -> list[tuple[str, str]]:
    live = views.open_efforts(records) - set(dormant)
    groups = {
        name: group
        for name, group in views.group_records(views.HOOK_VIEW, records, None).items()
        if name not in dormant
    }
    stamps = effort_position_stamps(records)
    stamped = sorted(n for n in groups if n in live and n in stamps)
    stamped.sort(key=stamps.__getitem__, reverse=True)
    unstamped = sorted(n for n in groups if n in live and n not in stamps)
    rest = sorted(n for n in groups if n not in live)
    sections: list[tuple[str, str]] = []
    for name in (*stamped, *unstamped, *rest):
        lines = views.group_lines(
            views.HOOK_VIEW, name, groups[name], [], records, link=False, progress=progress
        )
        label = name or ", ".join(views.group_subjects(groups[name]))
        sections.append((label, "\n".join(lines).rstrip()))
    return sections


def hook_constraints(
    records: list[Record], limit: int, dormant: Collection[str] = ()
) -> tuple[list[ConstraintLine], int]:
    live = views.open_efforts(records) - set(dormant)
    matches = effort_constraint_lines(records, live)
    return matches[:limit], len(matches)
