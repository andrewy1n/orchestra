"""Pure gate vocabulary for Needs you labels, prompts, next-step, and quiet."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol

from dashboard.backend.landing import Landing, phase_landing
from dashboard.backend.phase import PhaseRow
from dashboard.backend.snapshot import EffortView, NeedsYouItem
from dashboard.backend.task import TaskRow
from orchestra.conductor.attention import LandingFact

PLAN_REVIEW_PREFIX = "plan-review:"

_LOOP_SKILL = {
    "specify": "spec",
    "design": "design",
    "plan": "tasks",
    "execute": "execute",
    "integrate": "execute",
    "verify": "verify",
}


class _LandingState(Protocol):
    exists: bool
    merged: bool
    branch: str
    ahead: int


def plan_review_slug(item: NeedsYouItem) -> str | None:
    """Phase slug when the question scope is ``plan-review:<slug>``."""
    if item.kind not in ("blocking-question", "open-question"):
        return None
    if not item.text.startswith(PLAN_REVIEW_PREFIX):
        return None
    return item.text[len(PLAN_REVIEW_PREFIX) :]


# Compat alias for older call sites / tests.
_plan_review_slug = plan_review_slug


def _phase_title(view: EffortView, slug: str) -> str:
    for phase in view.phases:
        if phase.subject == slug:
            return phase.title
    return slug


def item_text(item: NeedsYouItem, view: EffortView) -> str:
    """Text beside the action label; phase title for plan-review scopes (R2)."""
    slug = _plan_review_slug(item)
    if slug is not None:
        return _phase_title(view, slug)
    return item.text


def action_label(item: NeedsYouItem, view: EffortView) -> str:
    """Action verb for a Needs you item (R1); plan-review uses Review plan (R2)."""
    if _plan_review_slug(item) is not None:
        return "Review plan"
    if item.kind in ("blocking-question", "open-question"):
        return "Answer"
    if item.kind == "needs-human":
        return "Decide"
    if item.kind == "unsigned-check":
        return "Sign off"
    if item.kind == "loop-route":
        return f"Route to {item.next}" if item.next else "Route to"
    if item.kind == "integration":
        return "Fix integration"
    if item.kind == "merge-branch":
        return "Merge branch"
    return item.kind


def prompt(item: NeedsYouItem, view: EffortView) -> str:
    """Ready agent string naming the effort, subject or phase, and action (R3)."""
    effort = view.effort
    slug = _plan_review_slug(item)
    if slug is not None:
        return f"Walk me through the plan for phase {slug} (effort {effort}) so I can review it."
    if item.kind == "unsigned-check":
        return f"Sign off the manual check for {item.subject} (effort {effort})."
    if item.kind == "blocking-question":
        return f"Answer the blocking question about {item.text} (effort {effort})."
    if item.kind == "open-question":
        return f"Answer the open question about {item.text} (effort {effort})."
    if item.kind == "needs-human":
        claim = f": {item.text}" if item.text else ""
        return f"Decide on the finding {item.subject} (effort {effort}){claim}."
    if item.kind == "loop-route":
        req = item.requirement or item.subject
        phase = item.phase or "phase"
        nxt = item.next or "next"
        return f"Route to {nxt} for {req} in phase {phase} (effort {effort})."
    if item.kind == "integration":
        phase = item.phase or item.subject
        result = item.result or "failed"
        return f"Fix the {result} integration for phase {phase} (effort {effort})."
    if item.kind == "merge-branch":
        phase = item.phase or item.subject
        return f"Merge the phase branch for phase {phase} (effort {effort})."
    return f"Act on {item.subject} (effort {effort})."


def _phase_tasks(view: EffortView, phase: str) -> list[TaskRow]:
    return [task for task in view.tasks if task.phase == phase and task.status != "withdrawn"]


def _has_decisions(phase: PhaseRow) -> bool:
    evidence = phase.evidence
    if evidence is None:
        return False
    return any(choice.choice for choice in evidence.decisions)


def _unmerged_done_slug(
    view: EffortView, landing: Mapping[str, Landing | _LandingState]
) -> str | None:
    for phase in sorted(view.phases, key=lambda row: row.ordinal):
        if phase.state != "done":
            continue
        state = landing.get(phase.subject)
        if state is not None and state.exists and not state.merged:
            return phase.subject
    return None


def next_step(view: EffortView, landing: dict[str, Landing]) -> str:
    """First matching R4 skill-named line (no `next:` prefix; position is UI-only)."""
    for item in view.needs_you:
        slug = _plan_review_slug(item)
        if slug is not None and item.kind == "blocking-question":
            return f"review the {slug} plan (tasks)"
        if item.kind == "blocking-question":
            return f"answer: {item.text}"

    merge_slug = _unmerged_done_slug(view, landing)
    if merge_slug is not None:
        return f"merge phase/{merge_slug} (verify)"

    for item in view.needs_you:
        if item.kind == "loop-route":
            nxt = item.next or "next"
            req = item.requirement or item.subject
            skill = _LOOP_SKILL.get(nxt, nxt)
            return f"{nxt} for {req} ({skill})"
        if item.kind == "unsigned-check":
            return f"sign off {item.subject} (verify)"

    running = [task for task in view.tasks if task.status == "running"]
    if running:
        waves = [task.wave for task in running if task.wave is not None]
        wave = min(waves) if waves else 0
        return f"wave {wave} running: {len(running)} tasks"

    ready = [task for task in view.tasks if task.status == "ready"]
    if ready:
        waves = [task.wave for task in ready if task.wave is not None]
        wave = min(waves) if waves else 0
        return f"execute wave {wave}"

    for phase in sorted(view.phases, key=lambda row: row.ordinal):
        if phase.state != "in_progress":
            continue
        tasks = _phase_tasks(view, phase.subject)
        if tasks and all(task.status == "done" for task in tasks):
            return f"close {phase.subject} (verify)"

    for phase in sorted(view.phases, key=lambda row: row.ordinal):
        if phase.state != "planned":
            continue
        if _has_decisions(phase):
            return f"tasks {phase.subject}"
        return f"spec {phase.subject}"

    if view.phases and all(phase.state == "done" for phase in view.phases):
        return "close the effort or add a phase"

    return ""


def is_quiet(task: TaskRow, now: datetime) -> bool:
    """True when a running task's last record is older than 2×estimate or 60m (R7)."""
    if task.status != "running":
        return False
    last = getattr(task, "last_record_at", None)
    if last is None:
        return False
    if task.estimate_minutes is not None:
        limit = timedelta(minutes=2 * task.estimate_minutes)
    else:
        limit = timedelta(minutes=60)
    return (now - last) > limit


def landing_for_view(root: Path, view: EffortView) -> dict[str, Landing]:
    """Compute phase_landing for each phase (same path the app and status use)."""
    landing: dict[str, Landing] = {}
    for phase in view.phases:
        state = phase_landing(root, phase.body, phase.subject)
        if state is not None:
            landing[phase.subject] = state
    return landing


def landing_facts(view: EffortView, root: Path) -> dict[str, LandingFact]:
    return {
        phase: LandingFact(state.exists, state.merged, state.branch, state.ahead)
        for phase, state in landing_for_view(root, view).items()
    }
