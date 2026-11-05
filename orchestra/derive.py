"""Derive requirement status, release readiness, phase progress and task assignment from records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.types import Record
from orchestra.score.requirements import (
    acceptance_requirement_ids,
    phase_requirements,
    phase_weight,
)

RequirementState = Literal["verified", "failed", "unverified"]

WORK_ITEM = "score:work-item"
EFFORT = "score:effort"
PHASE = "score:phase"
ACCEPTANCE = "score:acceptance"
SPECIFICATION = "score:specification"
CHECK_RUN = "tuner:check-run"
ASSESSMENT = "conductor:assessment"
ASSIGNMENT = "conductor:assignment"
QUESTION = "score:continuity-question"

_LIVE_WORK_STATES = ("planned", "in_progress", "done")
DORMANT_AFTER = timedelta(days=7)
Autonomy = Literal["gated", "auto-plan", "auto-phases"]


@dataclass(frozen=True)
class RequirementStatus:
    requirement: str
    status: RequirementState
    acceptance_ids: tuple[str, ...] = ()
    check_run_ids: tuple[str, ...] = ()
    assessment_id: str | None = None
    assessed: str | None = None


@dataclass(frozen=True)
class PhaseProgress:
    counts: dict[str, int] = field(default_factory=dict[str, int])
    done: int = 0
    total: int = 0
    in_progress: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskAssignment:
    assignee: str | None
    write_root: str | None


def _text(record: Record, key: str) -> str | None:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) and value else None


def _latest(records: list[Record]) -> Record | None:
    latest: Record | None = None
    for record in records:
        if latest is None or record["recorded_at"] >= latest["recorded_at"]:
            latest = record
    return latest


def _phase_work_items(records: list[Record], phase: str) -> list[Record]:
    return [
        r
        for r in records
        if r["record_type"] == WORK_ITEM
        and r["lifecycle_state"] in _LIVE_WORK_STATES
        and _text(r, "phase") == phase
    ]


def _phase_requirement_ids(records: list[Record], phase: str) -> list[str]:
    specs = [
        r
        for r in records
        if r["record_type"] == SPECIFICATION
        and r["lifecycle_state"] == "active"
        and _text(r, "phase") == phase
    ]
    if phase_weight(records, phase) == "light":
        return [rid for rid, _ in phase_requirements(records, phase)]
    spec = _latest(specs)
    sources = [spec] if spec is not None else _phase_work_items(records, phase)
    ids: list[str] = []
    for source in sources:
        value = record_payload(source).get("requirements")
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str) and item not in ids:
                ids.append(item)
    return ids


def _written_assessment(records: list[Record], phase: str, requirement: str) -> Record | None:
    return _latest(
        [
            r
            for r in records
            if r["record_type"] == ASSESSMENT
            and r["lifecycle_state"] == "active"
            and _text(r, "phase") == phase
            and _text(r, "requirement") == requirement
        ]
    )


def _derive_requirement(
    records: list[Record], phase: str, requirement: str, head: str | None
) -> RequirementStatus:
    acceptances = [
        r
        for r in records
        if r["record_type"] == ACCEPTANCE
        and r["lifecycle_state"] == "active"
        and _text(r, "phase") == phase
        and requirement in acceptance_requirement_ids(r)
    ]
    acceptance_ids = tuple(a["id"] for a in acceptances)
    latest_runs: list[Record] = []
    for acceptance in acceptances:
        runs = [
            r
            for r in records
            if r["record_type"] == CHECK_RUN
            and _text(r, "criterion_id") == acceptance["id"]
            and (head is None or _text(r, "revision") == head)
        ]
        latest = _latest(runs)
        if latest is not None:
            latest_runs.append(latest)
    results = [_text(r, "result") for r in latest_runs]
    status: RequirementState = "unverified"
    if "fail" in results:
        status = "failed"
    elif acceptances and len(latest_runs) == len(acceptances) and all(x == "pass" for x in results):
        status = "verified"
    return RequirementStatus(
        requirement=requirement,
        status=status,
        acceptance_ids=acceptance_ids,
        check_run_ids=tuple(r["id"] for r in latest_runs),
    )


def _passes_after(derived: RequirementStatus, written: Record, by_id: dict[str, Record]) -> bool:
    if derived.status != "verified":
        return False
    return all(
        by_id[run_id]["recorded_at"] > written["recorded_at"] for run_id in derived.check_run_ids
    )


def requirement_status(
    records: list[Record], phase: str, head: str | None = None
) -> dict[str, RequirementStatus]:
    by_id = {r["id"]: r for r in records}
    statuses: dict[str, RequirementStatus] = {}
    for requirement in _phase_requirement_ids(records, phase):
        derived = _derive_requirement(records, phase, requirement, head)
        written = _written_assessment(records, phase, requirement)
        written_status = _text(written, "status") if written is not None else None
        if (
            written is not None
            and written_status not in (None, "verified")
            and not _passes_after(derived, written, by_id)
        ):
            derived = RequirementStatus(
                requirement=requirement,
                status="failed" if written_status == "failed" else "unverified",
                acceptance_ids=derived.acceptance_ids,
                check_run_ids=derived.check_run_ids,
                assessment_id=written["id"],
                assessed=written_status,
            )
        statuses[requirement] = derived
    return statuses


def release_ready(records: list[Record], phase: str, head: str | None = None) -> bool:
    statuses = requirement_status(records, phase, head)
    return bool(statuses) and all(s.status == "verified" for s in statuses.values())


def phase_progress(records: list[Record], phase: str) -> PhaseProgress:
    items = _phase_work_items(records, phase)
    counts = {state: 0 for state in _LIVE_WORK_STATES}
    for item in items:
        counts[item["lifecycle_state"]] += 1
    return PhaseProgress(
        counts=counts,
        done=counts["done"],
        total=len(items),
        in_progress=tuple(i["subject"] for i in items if i["lifecycle_state"] == "in_progress"),
    )


def task_assignment(work_item: Record, records: list[Record]) -> TaskAssignment | None:
    assignee = _text(work_item, "assignee")
    write_root = _text(work_item, "write_root")
    if assignee is None or write_root is None:
        names = {work_item["id"], work_item["subject"]}
        written = _latest(
            [
                r
                for r in records
                if r["record_type"] == ASSIGNMENT and _text(r, "work_item") in names
            ]
        )
        if written is not None:
            assignee = assignee or _text(written, "assignee") or _text(written, "executor")
            write_root = write_root or _text(written, "write_root")
    if assignee is None and write_root is None:
        return None
    return TaskAssignment(assignee=assignee, write_root=write_root)


def _goal(records: list[Record], effort: str) -> Record | None:
    return _latest(
        [
            r
            for r in records
            if r["record_type"] == EFFORT
            and r["subject"] == effort
            and r["lifecycle_state"] != "superseded"
        ]
    )


def effort_autonomy(records: list[Record], effort: str) -> Autonomy:
    goal = _goal(records, effort)
    level = _text(goal, "autonomy") if goal is not None else None
    if level == "auto-plan":
        return "auto-plan"
    if level == "auto-phases":
        return "auto-phases"
    return "gated"


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def effort_dormant(records: list[Record], effort: str, now: datetime) -> bool:
    goal = _goal(records, effort)
    if goal is None or _text(goal, "status") == "closed":
        return False
    for record in records:
        if (
            record["record_type"] == PHASE
            and _text(record, "effort") == effort
            and record["lifecycle_state"] in ("planned", "in_progress")
        ):
            return False
    questions = [r for r in records if r["record_type"] == QUESTION and r["subject"] == effort]
    if any(
        r["lifecycle_state"] == "open" and record_payload(r).get("blocking") is True
        for r in questions
    ):
        return False
    touched = [
        _parse_time(r["recorded_at"])
        for r in records
        if _text(r, "effort") == effort
        or (r["record_type"] == EFFORT and r["subject"] == effort)
        or r in questions
    ]
    return bool(touched) and now - max(touched) >= DORMANT_AFTER
