"""Land one task: commit its worktree, record its evidence, and run its acceptance checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.execution_cost import (
    ExecutionCostError,
    landing_cost_fields,
    utc_now,
)
from orchestra.conductor.verification.check import run_check
from orchestra.conductor.verification.evidence.evidence import evidence_body, parse_evidence
from orchestra.conductor.wave import is_closing_task, task_acceptances
from orchestra.score.lookups import live_work_items
from orchestra.score.planning.work_item import WorkItem, current_work_item
from orchestra.score.workflow.workflow_blockers import (
    WorkflowBlockerError,
    blocked_tasks,
    phase_blockers,
)
from orchestra.tools import Git


class LandError(RuntimeError):
    """The task cannot land; the message names what to fix."""


@dataclass(frozen=True)
class CheckResult:
    acceptance_id: str
    subject: str
    check_run_id: str
    exit_code: int
    message: str = ""


@dataclass(frozen=True)
class LandedTask:
    task: str
    phase: str
    commit: str
    revision: str
    report_id: str
    checks: tuple[CheckResult, ...]
    evidence_result: str
    verdict: str = ""
    needs_human: bool = False


def in_progress_item(project: Project, task: str) -> WorkItem:
    records = project.records()
    item = current_work_item(task, records)
    if item is None or item.lifecycle_state != "in_progress":
        raise LandError(f"no in_progress work-item {task!r}")
    if item.phase:
        try:
            blockers = phase_blockers(records, item.phase)
        except WorkflowBlockerError as exc:
            raise LandError(str(exc)) from exc
        if task in blocked_tasks(live_work_items(item.phase, records), blockers):
            raise LandError(f"task {task!r} is blocked by a human decision")
    return item


def work_item(project: Project, task: str) -> Record:
    return in_progress_item(project, task).record


def _verify_evidence_revision(tree: Path, claimed: object) -> None:
    if not isinstance(claimed, str) or not claimed:
        return
    resolved = Git(tree).resolve(claimed)
    head = Git(tree).head()
    if resolved != head:
        raise LandError(
            f"evidence revision {claimed!r} is not the worktree HEAD {head[:12]}; "
            "return fresh evidence for the current tree"
        )


def _commit(tree: Path, phase: str, task: str) -> str:
    git = Git(tree)
    staged = git.run("diff", "--cached", "--name-only", "--", ".canon")
    if staged.stdout.strip():
        raise LandError(
            f"staged .canon changes would enter the task commit; unstage them: "
            f"{staged.stdout.split()[0]}"
        )
    status = git.run("status", "--porcelain", "--", ".", ":!.canon")
    if not status.stdout.strip():
        return ""
    added = git.run("add", "-A", "--", ".", ":!.canon")
    if added.returncode != 0:
        raise LandError(f"git add failed: {added.stderr.strip() or added.stdout.strip()}")
    committed = git.run("commit", "-q", "-m", f"feat({phase}): {task}")
    if committed.returncode != 0:
        raise LandError(f"commit failed: {committed.stderr.strip() or committed.stdout.strip()}")
    return Git(tree).head()


def acceptances_for(project: Project, task: str, phase: str) -> list[Record]:
    return task_acceptances(project.records(), task, phase)


def land(project: Project, repo: Path, task: str, evidence_path: Path) -> LandedTask:
    received_at = utc_now()
    evidence: JsonObject = parse_evidence(evidence_path)
    if evidence["subject"] != task:
        raise LandError(f"evidence subject {evidence['subject']!r} is not {task!r}")
    item = in_progress_item(project, task)
    phase = item.phase
    try:
        cost_fields = landing_cost_fields(
            item.record,
            evidence,
            received_at,
        )
    except ExecutionCostError as exc:
        raise LandError(str(exc)) from exc
    tree = Path(item.write_root or str(repo))
    closing = is_closing_task(project.records(), phase, item.record)
    if tree.is_dir():
        _verify_evidence_revision(tree, evidence.get("revision"))
    commit = "" if closing or not tree.is_dir() else _commit(tree, phase, task)
    try:
        revision = Git(tree).head()
    except RuntimeError as exc:
        raise LandError(str(exc)) from exc
    result = str(evidence["result"])
    payload: JsonObject = {
        "work_item": task,
        "result": result,
        "verdict": str(evidence["verdict"]),
        "revision": revision,
    }
    payload.update(cost_fields)
    body = evidence_body(evidence)
    repeats = [
        r
        for r in project.list("conductor:execution-report")
        if r["subject"] == task
        and record_payload(r).get("work_item") == task
        and record_payload(r).get("revision") == revision
        and record_payload(r).get("dispatch_id") == cost_fields.get("dispatch_id")
        and str(r.get("body") or "").strip() == body.strip()
    ]
    report = (
        repeats[-1]
        if repeats
        else project.create(
            record_type="conductor:execution-report", subject=task, payload=payload, body=body
        )
    )
    checks: list[CheckResult] = []
    for acceptance in sorted(acceptances_for(project, task, phase), key=lambda r: r["subject"]):
        outcome = run_check(
            acceptance_id=acceptance["id"],
            cwd=tree,
            project=project,
            execution_report=report["id"],
        )
        checks.append(
            CheckResult(
                acceptance["id"],
                acceptance["subject"],
                outcome.record["id"] if outcome.record else "",
                outcome.exit_code,
                outcome.message,
            )
        )
    return LandedTask(
        task,
        phase,
        commit,
        revision,
        report["id"],
        tuple(checks),
        result,
        str(evidence["verdict"]),
        evidence.get("needs_human") is True,
    )
