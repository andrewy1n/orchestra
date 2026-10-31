"""Task rows, task detail, and the check-run views they carry."""

from __future__ import annotations

from orchestra.canon import record_payload
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from orchestra.canon.project import Project
from dashboard.backend import store
from dashboard.backend.records import (
    CHECK_RESULT,
    INACTIVE_STATES,
    _derived,
    _items,
    _list,
    _merge_aliases,
    _recorded_at,
    _remapped,
    _section,
)
from dashboard.backend.store import ModelError


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


RELATED_TEXT = {
    "tuner:finding": ("finding", "claim"),
    "score:decision": ("decision", "choice"),
    "conductor:failed-attempt": ("failed-attempt", "attempted_action"),
    "tuner:investigation-observation": ("observation", "what_was_observed"),
}


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


def _check_from(record: dict[str, Any]) -> "CheckRun":
    payload = record_payload(record)
    return CheckRun(
        record["id"],
        payload.get("result", ""),
        payload.get("method", ""),
        payload.get("signed_by", ""),
        payload.get("revision", ""),
        _recorded_at(record),
        payload.get("evidence_kind") or "",
    )


def retry_max_redispatches(body: str) -> int:
    """Per-task re-dispatch budget from phase run facts, or the default of 2."""
    for line in (body or "").splitlines():
        if "retry_max_redispatches" not in line:
            continue
        _, _, rest = line.partition("retry_max_redispatches")
        rest = rest.lstrip(" \t:")
        token = rest.split()[0] if rest.split() else ""
        token = token.rstrip(".,;")
        if token.isdigit():
            return int(token)
    return DEFAULT_RETRY_MAX_REDISPATCHES


def _size(payload: dict[str, Any]) -> str:
    size = payload.get("size")
    return size if isinstance(size, str) and size else ""


def _estimate_minutes(payload: dict[str, Any]) -> int | None:
    if "estimate_minutes" not in payload:
        return None
    value = payload["estimate_minutes"]
    if value is None:
        return None
    return value


def _executor(payload: dict[str, Any]) -> str:
    executor = payload.get("executor")
    return executor if executor else "subagent"


def _attempts(payload: dict[str, Any]) -> int:
    if "attempts" not in payload:
        return 0
    value = payload["attempts"]
    if value is None or value == "":
        return 0
    return int(value)


def _task_status(record: dict[str, Any]) -> str | None:
    state = record["lifecycle_state"]
    if state == "planned":
        return "ready" if _derived(record).get("ready") else "waiting"
    return {"in_progress": "running", "done": "done", "withdrawn": "withdrawn"}.get(state)


def _assigned_at(assignments: list[dict[str, Any]], record: dict[str, Any]) -> datetime | None:
    names = {record["id"], record["subject"]}
    stamps = [_recorded_at(a) for a in assignments if record_payload(a).get("work_item") in names]
    return max(stamps, default=None)


def _task_assignments(
    assignments: list[dict[str, Any]], record: dict[str, Any]
) -> list[dict[str, Any]]:
    names = {record["id"], record["subject"]}
    return [a for a in assignments if record_payload(a).get("work_item") in names]


def _last_record_at(
    record: dict[str, Any],
    assignments: list[dict[str, Any]],
    amendments: list[dict[str, Any]],
    reports: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    others: list[str],
) -> datetime | None:
    """Latest assignment / amendment / execution-report / check-run stamp for a running task."""
    names = {record["id"], record["subject"]}
    mine = _task_assignments(assignments, record)
    stamps = [_recorded_at(a) for a in mine]
    assignment_names = names | {a["id"] for a in mine} | {a["subject"] for a in mine}
    stamps.extend(
        _recorded_at(a)
        for a in amendments
        if record_payload(a).get("assignment") in assignment_names
    )
    stamps.extend(_recorded_at(r) for r in reports if record_payload(r).get("work_item") in names)
    slug, effort = record["subject"], record_payload(record).get("effort", "")
    stamps.extend(_recorded_at(c) for c in checks if _belongs(c, slug, effort, others))
    return max(stamps, default=None)


def _depends(record: dict[str, Any]) -> list[str]:
    return record_payload(record).get("depends_on") or []


def _task_rows(
    records: list[dict[str, Any]],
    assignments: list[dict[str, Any]] | None = None,
    amendments: list[dict[str, Any]] | None = None,
    reports: list[dict[str, Any]] | None = None,
    checks: list[dict[str, Any]] | None = None,
    phases: list[dict[str, Any]] | None = None,
) -> list[TaskRow]:
    by_subject = {record["subject"]: record for record in sorted(records, key=_recorded_at)}
    assignments = assignments or []
    amendments = amendments or []
    reports = reports or []
    checks = checks or []
    budgets = {
        phase["subject"]: retry_max_redispatches(phase.get("body") or "")
        for phase in (phases or [])
    }
    subjects = [record["subject"] for record in records]
    rows = []
    for record in records:
        status = _task_status(record)
        if status is None:
            continue
        payload = record_payload(record)
        depends_on = [by_subject[ref] for ref in _items(_depends(record)) if ref in by_subject]
        running_since = _assigned_at(assignments, record) if status == "running" else None
        others = [s for s in subjects if s != record["subject"]]
        last_record_at = (
            _last_record_at(record, assignments, amendments, reports, checks, others)
            if running_since is not None
            else None
        )
        phase = payload.get("phase", "")
        rows.append(
            TaskRow(
                id=record["id"],
                subject=record["subject"],
                title=payload.get("title", ""),
                phase=phase,
                assignee=payload.get("assignee", ""),
                wave=_derived(record).get("wave"),
                status=status,
                waits_on=tuple(
                    dep["subject"] for dep in depends_on if dep["lifecycle_state"] != "done"
                ),
                depends_on=tuple(dep["id"] for dep in depends_on),
                running_since=running_since,
                size=_size(payload),
                estimate_minutes=_estimate_minutes(payload),
                executor=_executor(payload),
                last_record_at=last_record_at,
                attempts=_attempts(payload),
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


def _belongs(record: dict[str, Any], slug: str, effort: str, others: list[str]) -> bool:
    subject = record["subject"]
    if subject != slug and not subject.startswith(slug + "-"):
        return False
    if any(subject == other or subject.startswith(other + "-") for other in others):
        return False
    return record_payload(record).get("effort", effort) == effort


def _refers_to(record: dict[str, Any], key: str, names: set[str]) -> bool:
    return record_payload(record).get(key) in names


def _latest_checks(checks: list[dict[str, Any]]) -> dict[str, CheckRun]:
    latest: dict[str, CheckRun] = {}
    for record in sorted(checks, key=_recorded_at):
        if record["lifecycle_state"] in INACTIVE_STATES:
            continue
        payload = record_payload(record)
        latest[payload.get("criterion_id", "")] = _check_from(record)
    return latest


def _timeline(
    assignments: list[dict[str, Any]],
    amendments: list[dict[str, Any]],
    reports: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> list[TimelineEvent]:
    events = []
    for record in assignments:
        events.append(
            ("assignment", record, f"assigned to {record_payload(record).get('executor', '')}")
        )
    for record in amendments:
        events.append(("assignment-amendment", record, "amended"))
    for record in reports:
        payload = record_payload(record)
        events.append(("execution-report", record, f"reported {payload.get('verdict', '')}"))
    for record in checks:
        payload = record_payload(record)
        outcome = CHECK_RESULT.get(payload.get("result", ""), payload.get("result", ""))
        events.append(("check-run", record, f"{payload.get('method', '')} check {outcome}".strip()))
    timeline = [
        TimelineEvent(
            kind,
            record["id"],
            _recorded_at(record),
            summary,
            record.get("body") or "",
            record_payload(record).get("revision", "")
            if kind in ("execution-report", "check-run")
            else "",
        )
        for kind, record, summary in events
    ]
    timeline.sort(key=lambda event: event.recorded_at)
    return timeline


def _amendments_for(
    assignment: dict[str, Any],
    amendments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    keys = {assignment["id"], assignment["subject"]}
    matched = [record for record in amendments if record_payload(record).get("assignment") in keys]
    matched.sort(key=_recorded_at)
    return matched


def _report_for(
    assignment: dict[str, Any],
    reports: list[dict[str, Any]],
) -> dict[str, Any] | None:
    keys = {assignment["id"], assignment["subject"]}
    matched = [record for record in reports if record_payload(record).get("assignment") in keys]
    return max(matched, key=_recorded_at) if matched else None


def _agent_work(
    assignments: list[dict[str, Any]],
    amendments: list[dict[str, Any]],
    reports: list[dict[str, Any]],
) -> tuple[AgentWork, ...]:
    """Group assignment bodies, amendments by payload.assignment, and reports; newest first."""
    works: list[AgentWork] = []
    for record in sorted(assignments, key=_recorded_at, reverse=True):
        body = record.get("body") or ""
        assignment = AgentAssignment(
            id=record["id"],
            subject=record["subject"],
            recorded_at=_recorded_at(record),
            executor=record_payload(record).get("executor", ""),
            orientation=_section(body, "Orientation"),
            body=_without_section(body, "Orientation"),
        )
        amend_rows = tuple(
            AgentAmendment(
                record_a["id"],
                _recorded_at(record_a),
                _section(record_a.get("body") or "", "Correction"),
            )
            for record_a in _amendments_for(record, amendments)
        )
        report_record = _report_for(record, reports)
        report = None
        if report_record is not None:
            payload = record_payload(report_record)
            report = AgentReport(
                id=report_record["id"],
                recorded_at=_recorded_at(report_record),
                result=payload.get("result", ""),
                verdict=payload.get("verdict", ""),
                body=report_record.get("body") or "",
            )
        works.append(AgentWork(assignment, amend_rows, report))
    return tuple(works)


def load_task_detail(target: Project, work_item_id: str) -> TaskDetail:
    """Load one task's records with four CLI calls.

    `get` yields the subject, effort, body, and outbound depends_on; one `list --subject --full`
    yields every record for the slug; one work-item `list` for the effort names linked tasks; one goal `list` maps merged efforts.
    """
    item = store.get_record(target, work_item_id, "score:work-item")
    if "subject" not in item:
        raise ModelError(f"get score:work-item {work_item_id} returned unreadable output")
    aliases = _merge_aliases(_list(target, "score:effort"))
    item = _remapped([item], aliases)[0]
    slug, payload = item["subject"], record_payload(item)
    effort = payload.get("effort", "")
    records = _remapped(store.list_records(target, subject=slug), aliases)
    efforts = store.list_records(target, "score:work-item", payload={"effort": effort})
    rows = {row.id: row for row in _task_rows(efforts)}
    by_subject = {row.subject: row for row in rows.values()}
    mine = next((r for r in records if r["id"] == work_item_id), item)
    others = [
        r["subject"]
        for r in records
        if r["record_type"] == "score:work-item" and r["id"] != work_item_id
    ]
    names = {work_item_id, slug}
    of_type: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record["id"] != work_item_id and _belongs(record, slug, effort, others):
            of_type.setdefault(record["record_type"], []).append(record)
    assignments = [
        r for r in of_type.get("conductor:assignment", []) if _refers_to(r, "work_item", names)
    ]
    assignment_names = names | {r["id"] for r in assignments} | {r["subject"] for r in assignments}
    amendments = [
        r
        for r in of_type.get("conductor:assignment-amendment", [])
        if _refers_to(r, "assignment", assignment_names)
    ]
    reports = [
        r
        for r in of_type.get("conductor:execution-report", [])
        if _refers_to(r, "work_item", names)
    ]
    checks = of_type.get("tuner:check-run", [])
    latest = _latest_checks(checks)
    acceptances = [
        AcceptanceRow(
            r["id"],
            r["subject"],
            record_payload(r).get("criterion", ""),
            record_payload(r).get("method", ""),
            record_payload(r).get("verify_command", ""),
            latest.get(r["id"]),
        )
        for r in sorted(of_type.get("score:acceptance", []), key=_recorded_at)
    ]
    related = [
        RelatedRecord(kind, r["id"], r["subject"], record_payload(r).get(field, ""))
        for record_type, (kind, field) in RELATED_TEXT.items()
        for r in of_type.get(record_type, [])
    ]
    status = _task_status(mine) or mine["lifecycle_state"]
    return TaskDetail(
        id=work_item_id,
        subject=slug,
        effort=effort,
        title=payload.get("title", ""),
        status=status,
        phase=payload.get("phase", ""),
        wave=_derived(mine).get("wave"),
        assignee=payload.get("assignee", ""),
        body=item.get("body") or "",
        depends_on=_linked(
            [by_subject[ref].id for ref in _items(_depends(item)) if ref in by_subject], rows
        ),
        blocks=_linked((_derived(mine).get("referenced_by") or {}).get("depends_on", []), rows),
        acceptances=acceptances,
        timeline=_timeline(assignments, amendments, reports, checks),
        related=related,
        running_since=max(map(_recorded_at, assignments), default=None)
        if status == "running"
        else None,
        requirements=_items(payload.get("requirements")),
        decisions=_items(payload.get("decisions")),
        size=_size(payload),
        estimate_minutes=_estimate_minutes(payload),
        executor=_executor(payload),
        agent_work=_agent_work(assignments, amendments, reports),
    )
