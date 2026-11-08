from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from dashboard.backend.snapshot import Snapshot

WORK_NEXT_LIMIT = 5
_EPOCH = datetime.min.replace(tzinfo=timezone.utc)
_UNITS = (
    ("day", timedelta(days=1)),
    ("hour", timedelta(hours=1)),
    ("minute", timedelta(minutes=1)),
)


@dataclass(frozen=True)
class HubItem:
    kind: str
    effort: str
    subject: str
    title: str
    reason: str
    running: bool
    updated_at: datetime | None
    href: str
    step: str = ""


@dataclass
class HubView:
    work_next: list[HubItem] = field(default_factory=list)
    needs_you: list[HubItem] = field(default_factory=list)
    active_phases: list[HubItem] = field(default_factory=list)
    open_ideas: list[HubItem] = field(default_factory=list)
    generated_at: datetime | None = None


def relative_time(then: datetime | None, now: datetime) -> str:
    if then is None:
        return "a while ago"
    elapsed = max(now - then, timedelta())
    for name, size in _UNITS:
        count = elapsed // size
        if count >= 1:
            return f"{count} {name}{'' if count == 1 else 's'} ago"
    return "just now"


def _order(item: HubItem) -> tuple[bool, float, str, str]:
    stamp = item.updated_at or _EPOCH
    return (not item.running, -stamp.timestamp(), item.effort, item.subject)


def build_hub(snapshot: Snapshot, now: datetime) -> HubView:
    phases: list[HubItem] = []
    needs: list[HubItem] = []
    ideas: list[HubItem] = []
    for effort in snapshot.efforts:
        if effort.finished or effort.dormant:
            continue
        for phase in effort.phases:
            if phase.state != "in_progress":
                continue
            running = bool(phase.in_progress)
            phases.append(
                HubItem(
                    kind="phase",
                    effort=effort.effort,
                    subject=phase.subject,
                    title=phase.title,
                    reason="Running now"
                    if running
                    else f"Updated {relative_time(phase.updated_at, now)}",
                    running=running,
                    updated_at=phase.updated_at,
                    href=f"#/phase/{effort.effort}/{phase.subject}",
                    step=phase.evidence.stage if phase.evidence else "",
                )
            )
        for need in effort.needs_you:
            if need.status != "open":
                continue
            needs.append(
                HubItem(
                    kind="needs",
                    effort=effort.effort,
                    subject=need.id,
                    title=need.text,
                    reason=f"Needs you · updated {relative_time(need.updated_at, now)}",
                    running=False,
                    updated_at=need.updated_at,
                    href=f"#/needs/{effort.effort}/{need.id}",
                )
            )
        for idea in effort.backlog:
            if idea.status != "open":
                continue
            ideas.append(
                HubItem(
                    kind="idea",
                    effort=effort.effort,
                    subject=idea.id,
                    title=idea.text,
                    reason=f"Idea · parked {relative_time(idea.updated_at, now)}",
                    running=False,
                    updated_at=idea.updated_at,
                    href=f"#/backlog/{effort.effort}/{idea.id}",
                )
            )
    return HubView(
        work_next=sorted([*phases, *needs, *ideas], key=_order)[:WORK_NEXT_LIMIT],
        needs_you=sorted(needs, key=_order),
        active_phases=sorted(phases, key=_order),
        open_ideas=sorted(ideas, key=_order),
        generated_at=now,
    )
