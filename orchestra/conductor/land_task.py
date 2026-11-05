"""Land one task: commit its worktree, record its evidence, and run its acceptance checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.git_backend import run_git
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.check import git_head, run_check
from orchestra.conductor.evidence import evidence_body, parse_evidence
from orchestra.conductor.wave import closes_phase, phase_items


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


def _text(record: Record, key: str) -> str:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) else ""


def work_item(project: Project, task: str) -> Record:
    found = [
        r
        for r in project.list("score:work-item")
        if r["subject"] == task and r["lifecycle_state"] == "in_progress"
    ]
    if not found:
        raise LandError(f"no in_progress work-item {task!r}")
    return found[0]


def _verify_evidence_revision(tree: Path, claimed: object) -> None:
    if not isinstance(claimed, str) or not claimed:
        return
    resolved = run_git(
        tree, "rev-parse", "--verify", f"{claimed}^{{commit}}", capture_output=True, text=True
    )
    head = git_head(tree)
    if resolved.returncode != 0 or resolved.stdout.strip() != head:
        raise LandError(
            f"evidence revision {claimed!r} is not the worktree HEAD {head[:12]}; "
            "return fresh evidence for the current tree"
        )


def _commit(tree: Path, phase: str, task: str) -> str:
    staged = run_git(
        tree, "diff", "--cached", "--name-only", "--", ".canon", capture_output=True, text=True
    )
    if staged.stdout.strip():
        raise LandError(
            f"staged .canon changes would enter the task commit; unstage them: "
            f"{staged.stdout.split()[0]}"
        )
    status = run_git(
        tree, "status", "--porcelain", "--", ".", ":!.canon", capture_output=True, text=True
    )
    if not status.stdout.strip():
        return ""
    added = run_git(tree, "add", "-A", "--", ".", ":!.canon", capture_output=True, text=True)
    if added.returncode != 0:
        raise LandError(f"git add failed: {added.stderr.strip() or added.stdout.strip()}")
    committed = run_git(
        tree, "commit", "-q", "-m", f"feat({phase}): {task}", capture_output=True, text=True
    )
    if committed.returncode != 0:
        raise LandError(f"commit failed: {committed.stderr.strip() or committed.stdout.strip()}")
    return git_head(tree)


def acceptances_for(project: Project, task: str, phase: str) -> list[Record]:
    return [
        r
        for r in project.list("score:acceptance")
        if r["lifecycle_state"] == "active"
        and _text(r, "phase") == phase
        and (r["subject"] == task or r["subject"].startswith(task + "-"))
    ]


def land(project: Project, repo: Path, task: str, evidence_path: Path) -> LandedTask:
    evidence: JsonObject = parse_evidence(evidence_path)
    if evidence["subject"] != task:
        raise LandError(f"evidence subject {evidence['subject']!r} is not {task!r}")
    item = work_item(project, task)
    phase = _text(item, "phase")
    tree = Path(_text(item, "write_root") or str(repo))
    closing = closes_phase(item, phase_items(project.records(), phase))
    if tree.is_dir():
        _verify_evidence_revision(tree, evidence.get("revision"))
    commit = "" if closing or not tree.is_dir() else _commit(tree, phase, task)
    try:
        revision = git_head(tree)
    except RuntimeError as exc:
        raise LandError(str(exc)) from exc
    result = str(evidence["result"])
    report = project.create(
        record_type="conductor:execution-report",
        subject=task,
        payload={
            "work_item": task,
            "result": result,
            "verdict": str(evidence["verdict"]),
            "revision": revision,
        },
        body=evidence_body(evidence),
    )
    checks: list[CheckResult] = []
    for acceptance in sorted(acceptances_for(project, task, phase), key=lambda r: r["subject"]):
        outcome = run_check(
            acceptance_id=acceptance["id"],
            cwd=tree,
            store_root=project.project_root,
            store_dir=project.store_path,
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
