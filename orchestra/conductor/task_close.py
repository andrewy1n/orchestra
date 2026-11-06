"""Decide whether a landed task may close to done."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor import land_task, wave
from orchestra.conductor.close_batch import CloseRefused, CloseRequestError, build_batch

CODE_DONE = 0
CODE_FAILED = 1
CODE_PENDING_HUMAN = 3
MANUAL_EXIT = 3


@dataclass(frozen=True)
class Closure:
    state: str
    code: int
    reasons: tuple[str, ...]
    question_id: str = ""


def _red_check_run(project: Project, criterion: str, green: Record) -> str:
    earlier = [
        r
        for r in project.list("tuner:check-run")
        if record_payload(r).get("criterion_id") == criterion
        and record_payload(r).get("result") == "fail"
        and r["id"] != green["id"]
        and r["recorded_at"] <= green["recorded_at"]
    ]
    return max(earlier, key=lambda r: r["recorded_at"])["id"] if earlier else ""


def _policy_problem(
    project: Project, landed: land_task.LandedTask, item: Record, tree: Path
) -> str:
    criteria: list[JsonObject] = []
    for check in landed.checks:
        acceptance = project.get(check.acceptance_id, "score:acceptance")
        green = project.get(check.check_run_id, "tuner:check-run")
        entry: JsonObject = {
            "criterion_id": check.acceptance_id,
            "method": record_payload(acceptance).get("method"),
            "result": record_payload(green).get("result"),
            "check_run_id": check.check_run_id,
        }
        red = _red_check_run(project, check.acceptance_id, green)
        if entry["method"] == "tdd" and red:
            entry["red_check_run_id"] = red
            entry["revision"] = record_payload(green).get("revision")
        criteria.append(entry)

    def amendments(acceptance_id: str) -> list[Record]:
        subject = project.get(acceptance_id, "score:acceptance")["subject"]
        return [
            r
            for r in project.list("tuner:oracle-amendment")
            if r.get("lifecycle_state") in (None, "active")
            and record_payload(r).get("acceptance") in (acceptance_id, subject)
        ]

    request: JsonObject = {
        "subject": landed.task,
        "effort": str(record_payload(item).get("effort") or ""),
        "work_item_id": item["id"],
        "transition": "done",
        "acceptance_ids": [c.acceptance_id for c in landed.checks],
        "criteria": list(criteria),
        "execution_report_id": landed.report_id,
    }
    try:
        build_batch(
            request,
            cwd=tree,
            load_check_run=lambda cid: project.get(cid, "tuner:check-run"),
            load_acceptance=lambda aid: project.get(aid, "score:acceptance"),
            load_phase=lambda phase: wave.phase_record(project.records(), phase),
            list_oracle_amendments=amendments,
        )
    except (CloseRefused, CloseRequestError) as exc:
        return str(exc)
    return ""


def close(project: Project, landed: land_task.LandedTask, verified: frozenset[str]) -> Closure:
    item = land_task.work_item(project, landed.task)
    tree = Path(str(record_payload(item).get("write_root") or project.project_root))
    reasons: list[str] = []
    failed = False
    pending = False
    question_id = ""

    if landed.evidence_result != "pass":
        reasons.append(f"evidence result is {landed.evidence_result}")
        failed = True
    if landed.needs_human:
        question = wave.block(project, landed.phase, f"human:{landed.task}")
        question_id = question["id"]
        reasons.append("the executor reported needs_human; record and resolve the decision")
        pending = True
    elif landed.verdict != "pass":
        reasons.append(f"evidence verdict is {landed.verdict}, not pass")
        failed = True
    for check in landed.checks:
        if check.exit_code == MANUAL_EXIT:
            reasons.append(f"{check.subject}: manual acceptance needs a human sign-off")
            pending = True
        elif check.exit_code != 0:
            reasons.append(f"{check.subject}: {check.message or 'check failed'}")
            failed = True

    wanted = record_payload(item).get("requirements")
    required = [r for r in wanted if isinstance(r, str)] if isinstance(wanted, list) else []
    if not landed.checks and not required:
        reasons.append("no acceptance check ran and the task names no requirement")
        failed = True
    if not failed and not pending:
        unverified = [r for r in required if r not in verified]
        if unverified:
            reasons.append(f"requirements not verified: {', '.join(unverified)}")
            failed = True
    if not failed and not pending and landed.checks:
        problem = _policy_problem(project, landed, item, tree)
        if problem:
            reasons.append(problem)
            failed = True

    if failed or pending:
        return Closure(
            "in_progress",
            CODE_FAILED if failed else CODE_PENDING_HUMAN,
            tuple(reasons),
            question_id,
        )
    project.update(item["id"], record_type="score:work-item", transition="done")
    return Closure("done", CODE_DONE, (), question_id)
