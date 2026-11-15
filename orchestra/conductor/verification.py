from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor import land_task, wave
from orchestra.conductor.check import git_head, run_check
from orchestra.derive import requirement_status
from orchestra.tools import Git, ToolError


@dataclass(frozen=True)
class VerificationRun:
    checks: tuple[land_task.CheckResult, ...]
    verified: frozenset[str]
    refusal: str = ""


def _manual_check(project: Project, acceptance: Record, revision: str) -> Record | None:
    records = project.records()
    corrected = {
        record_id
        for record_id, values in project.derived(records).items()
        if values.get("corrected")
    }
    matches = [
        record
        for record in records
        if record["record_type"] == "tuner:check-run"
        and record["id"] not in corrected
        and record["payload"].get("criterion_id") == acceptance["id"]
        and record["payload"].get("method") == "manual"
        and record["payload"].get("revision") == revision
    ]
    return max(matches, key=lambda record: record["recorded_at"]) if matches else None


def _source_state(tree: Path) -> tuple[str, str]:
    head = git_head(tree)
    status = Git(tree).run("status", "--porcelain", "--untracked-files=all")
    if status.returncode != 0:
        raise RuntimeError(f"git status failed: {status.stderr or status.stdout}")
    return head, status.stdout


def run_closing_checks(project: Project, landed: land_task.LandedTask) -> VerificationRun:
    item = land_task.work_item(project, landed.task)
    tree = Path(str(item["payload"].get("write_root") or project.project_root))
    items = wave.phase_items(project.records(), landed.phase)
    if not wave.closes_phase(item, items):
        return VerificationRun((), frozenset(), "work-item is not the phase closing task")
    try:
        before = _source_state(tree)
    except (RuntimeError, ToolError) as exc:
        return VerificationRun((), frozenset(), str(exc))
    if before[0] != landed.revision:
        return VerificationRun((), frozenset(), "source HEAD changed before closing verification")
    if before[1]:
        return VerificationRun((), frozenset(), "source state is dirty before closing verification")
    acceptances = sorted(
        land_task.acceptances_for(project, landed.task, landed.phase),
        key=lambda record: record["subject"],
    )
    if not acceptances:
        return VerificationRun((), frozenset(), "no active acceptance checks")
    checks: list[land_task.CheckResult] = []
    for acceptance in acceptances:
        if acceptance["payload"].get("method") == "manual":
            manual = _manual_check(project, acceptance, landed.revision)
            signed = manual is not None and bool(manual["payload"].get("signed_by"))
            checks.append(
                land_task.CheckResult(
                    acceptance_id=acceptance["id"],
                    subject=acceptance["subject"],
                    check_run_id=manual["id"] if manual is not None and signed else "",
                    exit_code=(
                        0
                        if signed
                        and manual is not None
                        and manual["payload"].get("result") == "pass"
                        else 1
                        if signed
                        else 3
                    ),
                    message="" if signed else "manual acceptance needs a human sign-off",
                )
            )
            continue
        outcome = run_check(
            acceptance_id=acceptance["id"],
            cwd=tree,
            store_root=project.project_root,
            store_dir=project.store_path,
            execution_report=landed.report_id,
        )
        checks.append(
            land_task.CheckResult(
                acceptance_id=acceptance["id"],
                subject=acceptance["subject"],
                check_run_id=outcome.record["id"] if outcome.record else "",
                exit_code=outcome.exit_code,
                message=outcome.message,
            )
        )
        try:
            current = _source_state(tree)
        except (RuntimeError, ToolError) as exc:
            return VerificationRun(tuple(checks), frozenset(), str(exc))
        if current != before:
            return VerificationRun(
                tuple(checks),
                frozenset(),
                "source HEAD or working tree state changed during closing verification",
            )
    statuses = requirement_status(project.records(), landed.phase, head=landed.revision)
    verified = frozenset(
        requirement for requirement, status in statuses.items() if status.status == "verified"
    )
    return VerificationRun(tuple(checks), verified)
