from __future__ import annotations

from collections.abc import Collection, Mapping

from orchestra.canon import record_payload
from orchestra.canon.types import Record
from orchestra.conductor.phase_progress import PhaseProgress
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
    stamps = views.position_recorded_at(records)
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
) -> tuple[list[Record], int]:
    live = views.open_efforts(records) - set(dormant)
    role = next(r for r in views.BRIEF_ROLES if r.name == "constraint")
    matches = sorted(
        (
            r
            for r in records
            if r["record_type"] == role.record_type
            and role.select(r)
            and record_payload(r).get("effort") in live
        ),
        key=lambda r: r.get("subject") or "",
    )
    return matches[:limit], len(matches)
