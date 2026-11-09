"""Phase progress stages for the hub cards."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass

from dashboard.backend.landing import Landing
from dashboard.backend.phase import PhaseRow
from dashboard.backend.snapshot import NeedsYouItem
from dashboard.backend.task import TaskRow, run_fact_int

FULL_STAGES = ("spec", "design", "tasks", "execute", "verify", "review", "land", "close")
LIGHT_STAGES = FULL_STAGES[2:]
BLOCKER_LIMIT = 2
DEFAULT_FIX_TASK_LIMIT = 3
_FINISHED = ("done", "withdrawn")


@dataclass(frozen=True)
class Stage:
    id: str
    state: str


def derive_stages(
    *,
    weight: str,
    phase_state: str,
    approved: Collection[str],
    task_states: Sequence[str],
    requirement_statuses: Sequence[str],
    review_passed_at_head: bool,
    branch_merged: bool,
) -> list[Stage]:
    done = {
        "spec": "spec" in approved,
        "design": "design" in approved,
        "tasks": "plan" in approved,
        "execute": bool(task_states) and all(state == "done" for state in task_states),
        "verify": all(status == "verified" for status in requirement_statuses),
        "review": review_passed_at_head,
        "land": branch_merged,
        "close": phase_state == "done",
    }
    ids = LIGHT_STAGES if weight == "light" else FULL_STAGES
    stages: list[Stage] = []
    current_found = False
    for stage_id in ids:
        if done[stage_id]:
            state = "done"
        elif not current_found:
            state = "current"
            current_found = True
        else:
            state = "pending"
        stages.append(Stage(stage_id, state))
    return stages


@dataclass(frozen=True)
class TaskProgress:
    done: int
    running: int
    remaining: int
    total: int
    wave: int | None
    label: str


@dataclass(frozen=True)
class RequirementProgress:
    proven: int
    total: int
    label: str


@dataclass(frozen=True)
class RepairProgress:
    used: int
    limit: int
    label: str


@dataclass(frozen=True)
class BlockerSummary:
    shown: tuple[str, ...]
    more: int
    text: str


@dataclass(frozen=True)
class Progress:
    weight: str
    stages: tuple[Stage, ...]
    tasks: TaskProgress
    requirements: RequirementProgress
    repairs: RepairProgress | None
    blockers: BlockerSummary


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _blocker_summary(blockers: list[str]) -> BlockerSummary:
    shown = tuple(blockers[:BLOCKER_LIMIT])
    more = len(blockers) - len(shown)
    if not blockers:
        return BlockerSummary((), 0, "Nothing blocks close")
    text = "; ".join(shown) + (f" +{more} more" if more else "")
    return BlockerSummary(shown, more, text)


def build_progress(
    phase: PhaseRow,
    tasks: Sequence[TaskRow],
    needs: Sequence[NeedsYouItem],
    *,
    landing: Landing | None,
    approved: Collection[str],
    review_passed_at_head: bool,
) -> Progress:
    members = [t for t in tasks if t.phase == phase.subject and t.status != "withdrawn"]
    running = sum(1 for t in members if t.status == "running")
    unfinished_waves = [t.wave for t in members if t.status not in _FINISHED and t.wave is not None]
    wave = min(unfinished_waves) if unfinished_waves else None
    if phase.total == 0:
        label = "no tasks yet"
    else:
        label = f"{phase.done} of {phase.total} done"
        if wave is not None:
            label += f" · wave {wave}"
    task_progress = TaskProgress(
        done=phase.done,
        running=running,
        remaining=phase.total - phase.done - running,
        total=phase.total,
        wave=wave,
        label=label,
    )

    evidence = phase.evidence
    statuses = [row.status for row in evidence.requirements] if evidence else []
    proven = sum(1 for status in statuses if status == "verified")
    requirements = RequirementProgress(
        proven,
        len(statuses),
        f"{proven} of {len(statuses)} proven" if statuses else "no requirements",
    )

    fix_tasks = sum(1 for t in members if t.subject.startswith("fix-"))
    repairs = None
    if fix_tasks or any(t.attempts > 0 for t in members):
        limit = run_fact_int(phase.body, "retry_max_fix_tasks", DEFAULT_FIX_TASK_LIMIT)
        repairs = RepairProgress(fix_tasks, limit, f"{fix_tasks} of {limit} fix tasks used")

    blockers = [n.text for n in needs if n.phase == phase.subject and n.status == "open"]
    open_tasks = sum(1 for t in members if t.status != "done")
    if open_tasks:
        blockers.append(f"{_plural(open_tasks, 'task')} not done")
    if len(statuses) - proven:
        blockers.append(f"{_plural(len(statuses) - proven, 'requirement')} not proven")
    if not review_passed_at_head:
        blockers.append("No passing review")
    if landing is not None and not landing.merged:
        blockers.append("Branch not merged")

    task_states = [t.status for t in members]
    return Progress(
        weight=evidence.weight if evidence else "full",
        stages=tuple(
            derive_stages(
                weight=evidence.weight if evidence else "full",
                phase_state=phase.state,
                approved=approved,
                task_states=task_states,
                requirement_statuses=statuses,
                review_passed_at_head=review_passed_at_head,
                branch_merged=landing.merged if landing is not None else False,
            )
        ),
        tasks=task_progress,
        requirements=requirements,
        repairs=repairs,
        blockers=_blocker_summary(blockers),
    )
