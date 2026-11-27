from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.score.lookups import record_order
from orchestra.tools import Git
from orchestra.tools.errors import ToolError
from orchestra.tools.lsof import Lsof

ProcessLister = Callable[[Path], list[str]]


class ResumeError(ValueError):
    pass


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
    passed = {
        _text(run, "criterion_id")
        for run in project.list("tuner:check-run")
        if run["subject"] == task
        and _text(run, "result") == "pass"
        and _text(run, "revision") == head
    }
    return tuple(
        acceptance["id"]
        for acceptance in project.list("score:acceptance")
        if _belongs(acceptance, task)
        and acceptance["lifecycle_state"] == "active"
        and acceptance["id"] not in passed
    )


def _belongs(acceptance: Record, task: str) -> bool:
    subject = acceptance["subject"]
    return subject == task or subject.startswith(f"{task}-")


def resume(project: Project, task: str, *, list_processes: ProcessLister = holders) -> ResumeReport:
    item = _work_item(project, task)
    worktree = _text(item, "write_root")
    if not worktree:
        raise ResumeError(f"task {task!r} has no write_root")
    path = Path(worktree)
    dispatch_id = _text(item, "dispatch_id")
    reports = [
        report
        for report in project.list("conductor:execution-report")
        if report["subject"] == task and _text(report, "dispatch_id") == dispatch_id
    ]
    if dispatch_id and reports:
        raise ResumeError(
            f"task {task!r} has an execution report for dispatch {dispatch_id}; "
            "the executor finished"
        )
    try:
        running = list_processes(path)
    except (OSError, ToolError) as error:
        raise ResumeError(f"cannot prove the dispatch is inactive: {error}") from error
    if running:
        raise ResumeError(f"{', '.join(running)} holds the worktree {worktree}")
    git = Git(path)
    try:
        dirty = bool(git.status_porcelain().strip())
        head = git.head()
        phase = _text(item, "phase")
        base = f"phase/{phase}"
        ahead = int(git.text("rev-list", "--count", f"{base}..HEAD")) if phase else 0
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
