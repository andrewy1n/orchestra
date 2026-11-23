"""Task rows, task detail, and the check-run views they carry."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from dashboard.backend import store
from dashboard.backend.records import (
    INACTIVE_STATES,
    derived_values,
    list_records,
    recorded_at,
)
from dashboard.backend.store import ModelError
from orchestra.canon.project import Project
from orchestra.canon.project_config import load_project_config
from orchestra.canon.sections import body_section_ci
from orchestra.canon.types import Record
from orchestra.conductor.tasks.assignment import (
    ASSIGNMENT,
    assignments_of,
    referenced_assignment,
    referenced_work_item,
    task_assignment,
)
from orchestra.conductor.tasks.task_detail import (
    ASSIGNMENT_AMENDMENT_TYPE,
    EXECUTION_REPORT_TYPE,
    RELATED_KINDS,
    assignment_executor,
    related_text,
    report_facts,
    timeline_entries,
)
from orchestra.score.facts.detail_facts import ACCEPTANCE_TYPE, WORK_ITEM_TYPE, acceptance_facts
from orchestra.score.facts.work_item_facts import (
    executor_task,
    record_scope,
    task_plan,
    work_item_facts,
    work_item_status,
)
from orchestra.score.lookups import (
    LIVE_WORK_ITEM_STATES,
    dependencies,
    owning_work_item,
    record_order,
)
from orchestra.score.planning.effort import record_effort
from orchestra.score.planning.executor import (
    DEFAULT_SMALL_WAVE_BUDGET_MINUTES,
    task_executor,
)
from orchestra.tuner.evidence.evidence_facts import CHECK_RUN_TYPE
from orchestra.tuner.evidence.record_facts import check_run_facts

TASK_ORDER = ("running", "ready", "waiting", "done", "withdrawn")
DEFAULT_RETRY_MAX_REDISPATCHES = 2


@dataclass(frozen=True)
class TaskRow:
    id: str
    subject: str
    title: str
    phase: str
    assignee: str
    wave: int | None
    status: str
    waits_on: tuple[str, ...] = ()
    # Outbound dependency task record ids (for web graph edges).
    depends_on: tuple[str, ...] = ()
    running_since: datetime | None = None
    size: str = ""
    estimate_minutes: int | None = None
    executor: str = "subagent"
    last_record_at: datetime | None = None
    attempts: int = 0
    retry_budget: int = DEFAULT_RETRY_MAX_REDISPATCHES
    write_root: str = ""


@dataclass(frozen=True)
class LinkedTask:
    id: str
    subject: str
    title: str
    status: str


@dataclass(frozen=True)
class CheckRun:
    id: str
    result: str
    method: str
    signed_by: str
    revision: str
    recorded_at: datetime
    evidence_kind: str = ""


@dataclass(frozen=True)
class AcceptanceRow:
    id: str
    subject: str
    criterion: str
    method: str
    verify_command: str
    check: CheckRun | None


@dataclass(frozen=True)
class TimelineEvent:
    kind: str
    id: str
    recorded_at: datetime
    summary: str
    body: str
    revision: str = ""


@dataclass(frozen=True)
class RelatedRecord:
    kind: str
    id: str
    subject: str
    text: str


@dataclass(frozen=True)
class AgentAssignment:
    id: str
    subject: str
    recorded_at: datetime
    executor: str
    orientation: str
    body: str


@dataclass(frozen=True)
class AgentAmendment:
    id: str
    recorded_at: datetime
    correction: str


@dataclass(frozen=True)
class AgentReport:
    id: str
    recorded_at: datetime
    result: str
    verdict: str
    body: str


@dataclass(frozen=True)
class AgentWork:
    assignment: AgentAssignment
    amendments: tuple[AgentAmendment, ...]
    report: AgentReport | None


@dataclass(frozen=True)
class TaskDetail:
    id: str
    subject: str
    effort: str
    title: str
    status: str
    phase: str
    wave: int | None
    assignee: str
    body: str
    depends_on: list[LinkedTask]
    blocks: list[LinkedTask]
    acceptances: list[AcceptanceRow]
    timeline: list[TimelineEvent]
    related: list[RelatedRecord]
    running_since: datetime | None = None
    requirements: tuple[str, ...] = ()
    decisions: tuple[str, ...] = ()
    size: str = ""
    estimate_minutes: int | None = None
    executor: str = "subagent"
    agent_work: tuple[AgentWork, ...] = ()
    write_root: str = ""


def _without_section(body: str, heading: str) -> str:
    """Body with one ## heading section removed; other text kept as stored."""
    kept: list[str] = []
    skipping = False
    target = heading.strip().lower()
    for line in (body or "").splitlines():
        if line.startswith("## "):
            skipping = line[3:].strip().lower() == target
            if skipping:
                continue
        if not skipping:
            kept.append(line)
    return "\n".join(kept).strip()


def check_from(record: Record) -> CheckRun:
    facts = check_run_facts(record)
    return CheckRun(
        facts.id,
        facts.result,
        facts.method,
        facts.signed_by,
        facts.revision,
        recorded_at(record),
        facts.evidence_kind,
    )


def run_fact_int(body: str, name: str, default: int) -> int:
    for line in (body or "").splitlines():
        if name not in line:
            continue
        _, _, rest = line.partition(name)
        rest = rest.lstrip(" \t:")
        token = rest.split()[0] if rest.split() else ""
        token = token.rstrip(".,;")
        if token.isdigit():
            return int(token)
    return default


def retry_max_redispatches(body: str) -> int:
    """Per-task re-dispatch budget from phase run facts, or the default of 2."""
    return run_fact_int(body, "retry_max_redispatches", DEFAULT_RETRY_MAX_REDISPATCHES)


def configured_small_wave_budget(target: Project, records: list[Record]) -> int:
    requires_budget = any(
        record.get("lifecycle_state") == "planned" and task_plan(record).size in ("XS", "S")
        for record in records
    )
    if not requires_budget:
        return DEFAULT_SMALL_WAVE_BUDGET_MINUTES
    return load_project_config(target.project_root).small_wave_budget_minutes


def assigned_to(record: Record, assignments: list[Record]) -> tuple[str, str]:
    found = task_assignment(record, assignments)
    if found is None:
        return "", ""
    return found.assignee or "", found.write_root or ""


def _assigned_at(assignments: list[Record], record: Record) -> datetime | None:
    stamps = [recorded_at(a) for a in _task_assignments(assignments, record)]
    if stamps:
        return max(stamps)
    return recorded_at(record) if any(assigned_to(record, [])) else None


def _task_assignments(assignments: list[Record], record: Record) -> list[Record]:
    return assignments_of(record, assignments)


def _last_record_at(
    record: Record,
    assignments: list[Record],
    amendments: list[Record],
    reports: list[Record],
    checks: list[Record],
    work_items: list[Record],
) -> datetime | None:
    """Latest assignment / amendment / execution-report / check-run stamp for a running task."""
    names = {record["id"], record["subject"]}
    mine = _task_assignments(assignments, record)
    stamps = [recorded_at(a) for a in mine]
    assignment_names = names | {a["id"] for a in mine} | {a["subject"] for a in mine}
    stamps.extend(
        recorded_at(a) for a in amendments if referenced_assignment(a) in assignment_names
    )
    stamps.extend(recorded_at(r) for r in reports if referenced_work_item(r) in names)
    stamps.extend(recorded_at(c) for c in checks if belongs(c, record, work_items))
    return max(stamps, default=None)


def task_rows(
    records: list[Record],
    assignments: list[Record] | None = None,
    amendments: list[Record] | None = None,
    reports: list[Record] | None = None,
    checks: list[Record] | None = None,
    phases: list[Record] | None = None,
    *,
    small_wave_budget_minutes: int = DEFAULT_SMALL_WAVE_BUDGET_MINUTES,
) -> list[TaskRow]:
    by_subject = {record["subject"]: record for record in sorted(records, key=recorded_at)}
    assignments = assignments or []
    amendments = amendments or []
    reports = reports or []
    checks = checks or []
    budgets = {
        phase["subject"]: retry_max_redispatches(phase.get("body") or "")
        for phase in (phases or [])
    }
    wave_members: dict[tuple[str, int | None], list[Record]] = {}
    for item in records:
        if item.get("lifecycle_state") == "planned":
            wave = derived_values(item).get("wave")
            if type(wave) is not int:
                continue
            wave_members.setdefault((task_plan(item).phase, wave), []).append(item)
    rows: list[TaskRow] = []
    for record in records:
        status = work_item_status(record)
        if status is None:
            continue
        plan = task_plan(record)
        depends_on = [by_subject[ref] for ref in dependencies(record) if ref in by_subject]
        assignee, write_root = assigned_to(record, assignments)
        running_since = _assigned_at(assignments, record) if status == "running" else None
        last_record_at = (
            _last_record_at(record, assignments, amendments, reports, checks, records)
            if running_since is not None
            else None
        )
        phase = plan.phase
        task_facts = executor_task(record)
        if status in ("running", "done") and assignee in ("inline", "subagent"):
            task_facts = replace(task_facts, assignee=assignee)
        wave = derived_values(record).get("wave")
        wave_task_records = wave_members.get((phase, wave), []) if type(wave) is int else []
        rows.append(
            TaskRow(
                id=record["id"],
                subject=record["subject"],
                title=plan.title,
                phase=phase,
                assignee=assignee,
                write_root=write_root,
                wave=derived_values(record).get("wave"),
                status=status,
                waits_on=tuple(
                    dep["subject"] for dep in depends_on if dep["lifecycle_state"] != "done"
                ),
                depends_on=tuple(dep["id"] for dep in depends_on),
                running_since=running_since,
                size=plan.size,
                estimate_minutes=plan.estimate_minutes,
                executor=task_executor(
                    task_facts,
                    [executor_task(member) for member in wave_task_records] or [task_facts],
                    small_wave_budget_minutes=small_wave_budget_minutes,
                ),
                last_record_at=last_record_at,
                attempts=plan.attempts,
                retry_budget=budgets.get(phase, DEFAULT_RETRY_MAX_REDISPATCHES),
            )
        )
    rows.sort(
        key=lambda row: (
            TASK_ORDER.index(row.status),
            row.wave if row.wave is not None else 0,
            row.subject,
        )
    )
    return rows


def _linked(ids: list[str], rows: dict[str, TaskRow]) -> list[LinkedTask]:
    return [
        LinkedTask(row.id, row.subject, row.title, row.status) for i in ids if (row := rows.get(i))
    ]


def belongs(record: Record, task: Record, work_items: list[Record]) -> bool:
    phase = record_scope(task).phase
    candidates = [
        item
        for item in work_items
        if item["id"] == task["id"]
        or (item["lifecycle_state"] in LIVE_WORK_ITEM_STATES and record_scope(item).phase == phase)
    ]
    owner = owning_work_item(record["subject"], candidates)
    if owner is None or owner["id"] != task["id"]:
        return False
    effort = record_effort(task) or ""
    own = record_effort(record)
    return own is None or own == effort


def latest_checks(checks: list[Record]) -> dict[str, CheckRun]:
    latest: dict[str, CheckRun] = {}
    for record in sorted(checks, key=record_order):
        if record["lifecycle_state"] in INACTIVE_STATES:
            continue
        latest[check_run_facts(record).criterion_id] = check_from(record)
    return latest


def _timeline(
    assignments: list[Record],
    amendments: list[Record],
    reports: list[Record],
    checks: list[Record],
) -> list[TimelineEvent]:
    timeline = [
        TimelineEvent(
            entry.kind,
            entry.record["id"],
            recorded_at(entry.record),
            entry.summary,
            entry.record.get("body") or "",
            entry.revision,
        )
        for entry in timeline_entries(assignments, amendments, reports, checks)
    ]
    timeline.sort(key=lambda event: event.recorded_at)
    return timeline


def _amendments_for(
    assignment: Record,
    amendments: list[Record],
) -> list[Record]:
    keys = {assignment["id"], assignment["subject"]}
    matched = [record for record in amendments if referenced_assignment(record) in keys]
    matched.sort(key=recorded_at)
    return matched


def _report_for(
    assignment: Record,
    reports: list[Record],
) -> Record | None:
    keys = {assignment["id"], assignment["subject"]}
    matched = [record for record in reports if referenced_assignment(record) in keys]
    return max(matched, key=recorded_at) if matched else None


def _agent_work(
    assignments: list[Record],
    amendments: list[Record],
    reports: list[Record],
) -> tuple[AgentWork, ...]:
    """Group assignment bodies, amendments by payload.assignment, and reports; newest first."""
    works: list[AgentWork] = []
    for record in sorted(assignments, key=recorded_at, reverse=True):
        body = record.get("body") or ""
        assignment = AgentAssignment(
            id=record["id"],
            subject=record["subject"],
            recorded_at=recorded_at(record),
            executor=assignment_executor(record),
            orientation=body_section_ci(body, "Orientation"),
            body=_without_section(body, "Orientation"),
        )
        amend_rows = tuple(
            AgentAmendment(
                record_a["id"],
                recorded_at(record_a),
                body_section_ci(record_a.get("body") or "", "Correction"),
            )
            for record_a in _amendments_for(record, amendments)
        )
        report_record = _report_for(record, reports)
        report = None
        if report_record is not None:
            facts = report_facts(report_record)
            report = AgentReport(
                id=report_record["id"],
                recorded_at=recorded_at(report_record),
                result=facts.result,
                verdict=facts.verdict,
                body=report_record.get("body") or "",
            )
        works.append(AgentWork(assignment, amend_rows, report))
    return tuple(works)


def _acceptance_row(record: Record, check: CheckRun | None) -> AcceptanceRow:
    facts = acceptance_facts(record)
    return AcceptanceRow(
        record["id"],
        record["subject"],
        facts.criterion,
        facts.method,
        facts.verify_command,
        check,
    )


def load_task_detail(target: Project, work_item_id: str) -> TaskDetail:
    """Load one task's records with four CLI calls.

    `get` yields the subject, effort, body, and outbound depends_on; one `list --subject --full`
    yields every record for the slug; one work-item `list` for the effort names linked tasks.
    """
    item = store.get_record(target, work_item_id, WORK_ITEM_TYPE)
    if "subject" not in item:
        raise ModelError(f"get {WORK_ITEM_TYPE} {work_item_id} returned unreadable output")
    slug = item["subject"]
    facts = work_item_facts(item)
    plan = task_plan(item)
    effort = facts.scope.effort or ""
    records = store.list_records(target, subject=slug)
    efforts = store.list_records(target, WORK_ITEM_TYPE, payload={"effort": effort})
    effort_assignments = list_records(target, ASSIGNMENT)
    rows = {
        row.id: row
        for row in task_rows(
            efforts,
            effort_assignments,
            small_wave_budget_minutes=configured_small_wave_budget(target, efforts),
        )
    }
    by_subject = {row.subject: row for row in rows.values()}
    mine = next((r for r in records if r["id"] == work_item_id), item)
    work_items = [
        item,
        *(r for r in records if r["record_type"] == WORK_ITEM_TYPE and r["id"] != work_item_id),
    ]
    names = {work_item_id, slug}
    of_type: dict[str, list[Record]] = {}
    for record in records:
        if record["id"] != work_item_id and belongs(record, item, work_items):
            of_type.setdefault(record["record_type"], []).append(record)
    assignments = [r for r in of_type.get(ASSIGNMENT, []) if referenced_work_item(r) in names]
    assignment_names = names | {r["id"] for r in assignments} | {r["subject"] for r in assignments}
    amendments = [
        r
        for r in of_type.get(ASSIGNMENT_AMENDMENT_TYPE, [])
        if referenced_assignment(r) in assignment_names
    ]
    reports = [
        r for r in of_type.get(EXECUTION_REPORT_TYPE, []) if referenced_work_item(r) in names
    ]
    checks = of_type.get(CHECK_RUN_TYPE, [])
    latest = latest_checks(checks)
    acceptances = [
        _acceptance_row(r, latest.get(r["id"]))
        for r in sorted(of_type.get(ACCEPTANCE_TYPE, []), key=recorded_at)
    ]
    related = [
        RelatedRecord(kind, r["id"], r["subject"], related_text(r))
        for record_type, kind in RELATED_KINDS.items()
        for r in of_type.get(record_type, [])
    ]
    status = work_item_status(mine) or mine["lifecycle_state"]
    assignee, write_root = assigned_to(item, assignments)
    return TaskDetail(
        id=work_item_id,
        subject=slug,
        effort=effort,
        title=plan.title,
        status=status,
        phase=facts.scope.phase or "",
        wave=derived_values(mine).get("wave"),
        assignee=assignee,
        write_root=write_root,
        body=item.get("body") or "",
        depends_on=_linked(
            [by_subject[ref].id for ref in dependencies(item) if ref in by_subject], rows
        ),
        blocks=_linked(
            (derived_values(mine).get("referenced_by") or {}).get("depends_on", []), rows
        ),
        acceptances=acceptances,
        timeline=_timeline(assignments, amendments, reports, checks),
        related=related,
        running_since=_assigned_at(assignments, mine) if status == "running" else None,
        requirements=facts.requirements,
        decisions=facts.decisions,
        size=plan.size,
        estimate_minutes=plan.estimate_minutes,
        executor=rows[work_item_id].executor,
        agent_work=_agent_work(assignments, amendments, reports),
    )
