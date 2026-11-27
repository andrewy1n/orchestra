from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor.landing.landing import phase_place
from orchestra.conductor.verification.evidence import head_evidence
from orchestra.score.lookups import owning_work_item, record_order
from orchestra.score.planning.phase import current_phase_model
from orchestra.tools import Git
from orchestra.tools.errors import ToolError
from orchestra.tools.lsof import Lsof

ProcessLister = Callable[[Path], list[str]]


class ResumeError(ValueError):
    pass


def _hint(task: str) -> str:
    return f"; open a blocking continuity-question with scope retry:{task} and do not resume"


@dataclass(frozen=True)
class ResumeReport:
    task: str
    worktree: str
    step: str
    commits_ahead: int
    dirty: bool
    pending_acceptances: tuple[str, ...]


def holders(worktree: Path) -> list[str]:
    return Lsof(worktree.parent).holders(worktree)


def _work_item(project: Project, task: str) -> Record:
    items = [
        record
        for record in project.list("score:work-item")
        if record["subject"] == task and record["lifecycle_state"] != "superseded"
    ]
    if not items:
        raise ResumeError(f"work-item {task!r} not found")
    item = max(items, key=record_order)
    if item["lifecycle_state"] != "in_progress":
        raise ResumeError(f"task {task!r} must be in_progress to resume")
    return item


def _text(record: Record, key: str) -> str:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) else ""


def _pending(project: Project, task: str, head: str) -> tuple[str, ...]:
    records = project.records()
    index = head_evidence.EvidenceIndex(records)
    items = [
        record
        for record in records
        if record["record_type"] == "score:work-item" and record["lifecycle_state"] != "superseded"
    ]
    return tuple(
        acceptance["id"]
        for acceptance in project.list("score:acceptance")
        if acceptance["lifecycle_state"] == "active"
        and _owner(acceptance, items) == task
        and not head_evidence.acceptance_runner_at_head(index, acceptance, head).holds
    )


def _owner(acceptance: Record, items: list[Record]) -> str | None:
    owner = owning_work_item(acceptance["subject"], items)
    return owner["subject"] if owner is not None else None


def resume(project: Project, task: str, *, list_processes: ProcessLister = holders) -> ResumeReport:
    item = _work_item(project, task)
    worktree = _text(item, "write_root")
    if not worktree:
        raise ResumeError(f"task {task!r} has no write_root")
    path = Path(worktree)
    dispatch_id = _text(item, "dispatch_id")
    if not dispatch_id:
        raise ResumeError(
            f"task {task!r} has no dispatch id, so no dispatch can be proven inactive{_hint(task)}"
        )
    phase_slug = _text(item, "phase")
    phase = current_phase_model(phase_slug, project.records()) if phase_slug else None
    if phase is None:
        raise ResumeError(f"task {task!r} has no known phase{_hint(task)}")
    reports = [
        report
        for report in project.list("conductor:execution-report")
        if report["subject"] == task and _text(report, "dispatch_id") == dispatch_id
    ]
    if reports:
        raise ResumeError(
            f"task {task!r} has an execution report for dispatch {dispatch_id}; "
            f"the executor finished{_hint(task)}"
        )
    try:
        running = list_processes(path)
    except (OSError, ToolError) as error:
        raise ResumeError(f"cannot prove the dispatch is inactive: {error}{_hint(task)}") from error
    if running:
        raise ResumeError(f"{', '.join(running)} holds the worktree {worktree}{_hint(task)}")
    git = Git(path)
    try:
        dirty = bool(git.status_porcelain().strip())
        head = git.head()
        base = phase_place(phase, git.primary_checkout()).branch
        ahead = int(git.text("rev-list", "--count", f"{base}..HEAD"))
    except (ToolError, ValueError) as error:
        raise ResumeError(f"cannot read the worktree {worktree}: {error}") from error
    pending = _pending(project, task, head)
    if dirty:
        step = "land"
    elif ahead == 0:
        step = "implement"
    elif pending:
        step = "check"
    else:
        step = "close"
    return ResumeReport(task, worktree, step, ahead, dirty, pending)
