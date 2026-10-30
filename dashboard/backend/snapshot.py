"""Dashboard snapshot built from canon records, one list per record type."""

from __future__ import annotations

from orchestra.canon import record_payload
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from orchestra.canon.project import Project
from dashboard.backend import store
from dashboard.backend.journal import load_journal, ordered as journal_ordered
from dashboard.backend.phase import (
    MilestoneRow, PhaseRow, _latest_assessment_map, _milestone_rows, _phase_evidence, _phase_rows, attach_milestones,
)
from dashboard.backend.records import (
    CHECK_RESULT, INACTIVE_STATES, _by_effort, _derived, _list, _live, _merge_aliases, _newest,
    _recorded_at, _remapped,
)
from dashboard.backend.store import change_token
from dashboard.backend.task import TaskRow, _task_rows


RECENT = timedelta(hours=24)
NEEDS_ORDER = (
    "blocking-question", "loop-route", "integration", "merge-branch",
    "needs-human", "unsigned-check", "open-question",
)
FULL_TYPES = (
    "score:continuity-question", "tuner:finding", "tuner:check-run", "score:work-item",
    "score:phase", "score:specification", "conductor:assessment", "conductor:integration-report",
    "conductor:proof-packet", "composer:idea",
)
UPSTREAM_NEXT = frozenset({"specify", "design", "plan"})
PLACEMENT_TYPE = "composer:placement"


@dataclass(frozen=True)
class NeedsYouItem:
    kind: str
    id: str
    subject: str
    text: str
    record_type: str = ""
    body: str = ""
    task_id: str = ""
    phase: str = ""
    requirement: str = ""
    status: str = ""
    next: str = ""
    result: str = ""
    revision: str = ""


@dataclass(frozen=True)
class BacklogItem:
    id: str
    subject: str
    effort: str
    text: str
    status: str = "open"
    source: str = ""
    phase: str = ""
    body: str = ""
    record_type: str = "composer:idea"


@dataclass(frozen=True)
class ActivityItem:
    kind: str
    id: str
    subject: str
    recorded_at: datetime
    summary: str
    failed: bool = False


@dataclass
class EffortView:
    effort: str
    goal: str
    phases: list[PhaseRow] = field(default_factory=list)
    milestones: list[MilestoneRow] = field(default_factory=list)
    tasks: list[TaskRow] = field(default_factory=list)
    needs_you: list[NeedsYouItem] = field(default_factory=list)
    activity: list[ActivityItem] = field(default_factory=list)
    release_ready: bool = False
    position: str = ""
    kind: str = ""
    journal_open: list = field(default_factory=list)
    backlog: list[BacklogItem] = field(default_factory=list)
    area: str = ""

    @property
    def finished(self) -> bool:
        counted = [task for task in self.tasks if task.status != "withdrawn"]
        if not self.phases and not counted:
            return False
        return all(phase.state == "done" for phase in self.phases) and all(task.status == "done" for task in counted)


@dataclass
class Snapshot:
    efforts: list[EffortView]
    token: str
    generated_at: datetime


_SNAPSHOT_TYPES = (
    "score:effort", "score:phase", "score:milestone", "score:work-item",
    "score:continuity-question",
    "tuner:finding", "tuner:check-run", "conductor:assignment", "conductor:assignment-amendment",
    "conductor:execution-report",
    "score:specification", "score:design", "conductor:assessment", "conductor:integration-report", "conductor:release",
    "score:position", "composer:idea", PLACEMENT_TYPE,
)


def _list_all(target: Project, record_types: tuple[str, ...], token: str) -> dict[str, list[dict[str, Any]]]:
    def load(record_type: str) -> list[dict[str, Any]]:
        with store.pinned_token(token):
            return _list(target, record_type)

    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(zip(record_types, pool.map(load, record_types)))


def _structured_phases(specs: list[dict[str, Any]]) -> set[tuple[str, str]]:
    found = set()
    for record in _live(specs):
        payload = record_payload(record)
        effort, phase = payload.get("effort") or "", payload.get("phase") or ""
        if effort and phase:
            found.add((effort, phase))
    return found


def _needs_route(record: dict[str, Any]) -> bool:
    payload = record_payload(record)
    status, nxt, confidence = payload.get("status", ""), payload.get("next", ""), payload.get("confidence", "")
    if status == "insufficient" or nxt == "execute":
        return False
    if nxt == "verify" and status != "blocked":
        return False
    return nxt in UPSTREAM_NEXT or status == "blocked" or confidence == "low"


def _assessment_summary(record: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> tuple[str, bool]:
    payload = record_payload(record)
    summary = f"{payload.get('requirement', '')} {payload.get('status', '')} {payload.get('next', '')}"
    if payload.get("next") in UPSTREAM_NEXT:
        summary += " upstream"
    links = (record.get("relationships") or {}).get("supersedes") or []
    previous = by_id.get(links[0]) if links else None
    if previous is not None:
        old, new = record_payload(previous).get("level") or "", payload.get("level") or ""
        if old != new:
            summary += f" level {old} to {new}"
    return summary, payload.get("status") in ("failed", "blocked")


def _task_for(subject: str, tasks: list[dict[str, Any]]) -> str:
    matches = [task for task in tasks if subject == task["subject"] or subject.startswith(task["subject"] + "-")]
    return max(matches, key=lambda task: len(task["subject"]))["id"] if matches else ""


def _backlog_text(record: dict[str, Any]) -> str:
    for line in (record.get("body") or "").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return record.get("subject") or ""


def _backlog_items(records: list[dict[str, Any]]) -> list[BacklogItem]:
    items = []
    for record in records:
        if record.get("lifecycle_state") in INACTIVE_STATES:
            continue
        payload = record_payload(record)
        if payload.get("status") != "open":
            continue
        items.append(BacklogItem(
            id=record["id"],
            subject=record["subject"],
            effort=payload.get("effort") or "",
            text=_backlog_text(record),
            status=payload.get("status") or "open",
            source=payload.get("source") or "",
            phase=payload.get("phase") or "",
            body=record.get("body") or "",
            record_type=record.get("record_type") or "composer:idea",
        ))
    items.sort(key=lambda item: (item.subject, item.id))
    return items


def _needs_you(
    questions: list[dict[str, Any]], findings: list[dict[str, Any]], checks: list[dict[str, Any]],
    acceptances: dict[str, dict[str, Any]] | None = None, tasks: list[dict[str, Any]] | None = None,
    assessments: list[dict[str, Any]] | None = None, integrations: list[dict[str, Any]] | None = None,
    spec_phases: set[str] | None = None,
) -> list[NeedsYouItem]:
    acceptances = acceptances or {}
    tasks = tasks or []

    def item(kind: str, record: dict[str, Any], subject: str, text: str) -> NeedsYouItem:
        return NeedsYouItem(
            kind, record["id"], subject, text, record_type=record.get("record_type", ""),
            body=record.get("body") or "", task_id=_task_for(subject, tasks),
            revision=record.get("revision") or "",
        )

    items = []
    for record in questions:
        if record["lifecycle_state"] == "open":
            kind = "blocking-question" if record_payload(record).get("blocking") is True else "open-question"
            items.append(item(kind, record, record["subject"], record_payload(record).get("scope", "")))
    for record in findings:
        if record_payload(record).get("needs") == "human" and record["lifecycle_state"] in ("asserted", "supported", "disputed"):
            items.append(item("needs-human", record, record["subject"], record_payload(record).get("claim", "")))
    for record in checks:
        payload = record_payload(record)
        if payload.get("method") == "manual" and payload.get("signed_by") == "" and not _derived(record).get("corrected"):
            acceptance = acceptances.get(payload.get("criterion_id", ""))
            subject = acceptance["subject"] if acceptance else record["subject"]
            criterion = record_payload(acceptance).get("criterion", "") if acceptance else ""
            text = f"{criterion} {payload.get('result', '')}".strip()
            items.append(item("unsigned-check", record, subject, text))
    spec_phases = spec_phases or set()
    for (phase, requirement), record in sorted(_latest_assessment_map(assessments or []).items()):
        if phase not in spec_phases or not _needs_route(record):
            continue
        payload = record_payload(record)
        status, nxt = payload.get("status", ""), payload.get("next", "")
        text = " ".join(part for part in (requirement, status, nxt) if part)
        items.append(NeedsYouItem(
            "loop-route", record["id"], record["subject"], text, record_type=record.get("record_type", ""),
            phase=phase, requirement=requirement, status=status, next=nxt,
            revision=record.get("revision") or "",
        ))
    reports_by_phase: dict[str, list[dict[str, Any]]] = {}
    for record in _live(integrations or []):
        phase = record_payload(record).get("phase", "")
        if phase in spec_phases:
            reports_by_phase.setdefault(phase, []).append(record)
    for phase, records in reports_by_phase.items():
        latest = _newest(records)
        if latest is None:
            continue
        result = record_payload(latest).get("result", "")
        if result not in ("fail", "blocked"):
            continue
        items.append(NeedsYouItem(
            "integration", latest["id"], latest["subject"], f"{phase} {result}",
            record_type=latest.get("record_type", ""), phase=phase, result=result,
            revision=latest.get("revision") or "",
        ))
    items.sort(key=lambda entry: NEEDS_ORDER.index(entry.kind))
    return items


def _activity(
    assignments: list[dict[str, Any]], reports: list[dict[str, Any]], checks: list[dict[str, Any]],
    efforts_by_work_item: dict[str, tuple[str, str]], since: datetime,
    assessments: list[dict[str, Any]] | None = None, integrations: list[dict[str, Any]] | None = None,
    releases: list[dict[str, Any]] | None = None, structured: set[tuple[str, str]] | None = None,
) -> dict[str, list[ActivityItem]]:
    by_effort: dict[str, list[ActivityItem]] = {}

    def add(effort: str | None, kind: str, record: dict[str, Any], summary: str, failed: bool = False) -> None:
        if effort is not None and _recorded_at(record) >= since:
            by_effort.setdefault(effort, []).append(
                ActivityItem(kind, record["id"], record["subject"], _recorded_at(record), summary, failed)
            )

    def work_item(record: dict[str, Any]) -> tuple[str | None, str]:
        ref = record_payload(record).get("work_item", "")
        effort, subject = efforts_by_work_item.get(ref, (None, ref))
        return effort, subject

    for record in assignments:
        effort, subject = work_item(record)
        add(record_payload(record).get("effort") or effort, "assignment", record,
            f"{subject} assigned to {record_payload(record).get('executor', '')}")
    for record in reports:
        effort, subject = work_item(record)
        payload = record_payload(record)
        add(effort, "execution-report", record, f"{subject} reported {payload.get('verdict', '')}",
            "fail" in (payload.get("result"), payload.get("verdict")))
    for record in checks:
        payload = record_payload(record)
        outcome = CHECK_RESULT.get(payload.get("result", ""), payload.get("result", ""))
        method = payload.get("method", "").replace("check", "").strip()
        label = " ".join(part for part in (record["subject"], method, "check", outcome) if part)
        add(payload.get("effort"), "check-run", record, label, payload.get("result") == "fail")
    structured = structured or set()
    assessment_by_id = {record["id"]: record for record in assessments or []}
    for record in assessments or []:
        payload = record_payload(record)
        if (payload.get("effort"), payload.get("phase")) not in structured:
            continue
        summary, failed = _assessment_summary(record, assessment_by_id)
        add(payload.get("effort"), "assessment", record, summary, failed)
    for record in integrations or []:
        payload = record_payload(record)
        if (payload.get("effort"), payload.get("phase")) not in structured:
            continue
        result = payload.get("result", "")
        add(payload.get("effort"), "integration", record, f"{payload.get('phase', '')} {result}", result in ("fail", "blocked"))
    for record in releases or []:
        payload = record_payload(record)
        if (payload.get("effort"), payload.get("phase")) not in structured:
            continue
        state = payload.get("state", "")
        add(payload.get("effort"), "release", record, f"{payload.get('phase', '')} {state}", state == "failed")
    for items in by_effort.values():
        items.sort(key=lambda item: item.recorded_at, reverse=True)
    return by_effort


def load_snapshot(target: Project, now: datetime | None = None, token: str | None = None) -> Snapshot:
    token = token or change_token(target)
    with store.pinned_token(token):
        return _load_snapshot(target, now or datetime.now(timezone.utc), token)


def _load_snapshot(target: Project, now: datetime, token: str) -> Snapshot:
    listed = _list_all(target, _SNAPSHOT_TYPES, token)
    aliases = _merge_aliases(listed["score:effort"])
    listed = {record_type: _remapped(records, aliases) for record_type, records in listed.items()}
    goals = [
        r for r in listed["score:effort"]
        if r["lifecycle_state"] == "active" and record_payload(r).get("status") != "closed"
    ]
    phases = _by_effort(listed["score:phase"])
    milestones = _by_effort(listed.get("score:milestone") or [])
    all_tasks = listed["score:work-item"]
    tasks = _by_effort(all_tasks)
    questions = _by_effort(listed["score:continuity-question"], "subject")
    findings = _by_effort(listed["tuner:finding"])
    checks_all = listed["tuner:check-run"]
    checks = _by_effort(checks_all)
    acceptances_all = _remapped(_list(target, "score:acceptance"), aliases)
    acceptances = _by_effort(acceptances_all)
    acceptances_by_id = {record["id"]: record for record in acceptances_all}
    efforts_by_work_item = {}
    for task in all_tasks:
        entry = (record_payload(task).get("effort"), task["subject"])
        efforts_by_work_item[task["id"]] = entry
        efforts_by_work_item.setdefault(task["subject"], entry)
    specs = listed["score:specification"]
    designs = listed["score:design"]
    assessments = listed["conductor:assessment"]
    integrations = listed["conductor:integration-report"]
    releases = listed["conductor:release"]
    backlog_by_effort = _by_effort(listed.get("composer:idea") or [])
    decisions = _remapped(_list(target, "score:decision"), aliases) if designs else []
    structured = _structured_phases(specs)
    specs_by_effort = _by_effort(specs)
    designs_by_effort = _by_effort(designs)
    assessments_by_effort = _by_effort(assessments)
    integrations_by_effort = _by_effort(integrations)
    releases_by_effort = _by_effort(releases)
    decisions_by_effort = _by_effort(decisions)
    activity = _activity(
        listed["conductor:assignment"], listed["conductor:execution-report"], checks_all,
        efforts_by_work_item, now - RECENT, assessments, integrations, releases, structured,
    )
    positions = {
        record["subject"]: record_payload(record).get("position", "")
        for record in listed["score:position"]
        if record["lifecycle_state"] == "active"
        and record_payload(record).get("status") != "closed"
        and record_payload(record).get("scope") == "effort"
    }
    areas = {
        record["subject"]: record_payload(record).get("area") or ""
        for record in _live(listed[PLACEMENT_TYPE])
    }
    efforts = []
    for goal in sorted(goals, key=lambda record: record["subject"]):
        effort = goal["subject"]
        effort_tasks = tasks.get(effort, [])
        effort_acceptances = acceptances.get(effort, [])
        effort_checks = checks.get(effort, [])
        evidence_by_phase = {}
        for spec_effort, phase in structured:
            if spec_effort != effort:
                continue
            evidence = _phase_evidence(
                phase, effort, specs_by_effort.get(effort, []), designs_by_effort.get(effort, []),
                decisions_by_effort.get(effort, []), effort_tasks, effort_acceptances, effort_checks,
                assessments_by_effort.get(effort, []), integrations_by_effort.get(effort, []),
                releases_by_effort.get(effort, []),
            )
            if evidence is not None:
                evidence_by_phase[phase] = evidence
        phase_rows = _phase_rows(
            phases.get(effort, []), effort_tasks, effort_acceptances, effort_checks, evidence_by_phase,
        )
        milestone_rows = _milestone_rows(milestones.get(effort, []), phase_rows)
        phase_rows = attach_milestones(phase_rows, milestone_rows)
        kind = record_payload(goal).get("kind") or ""
        journal_open = []
        if kind in ("repair", "evaluate"):
            open_items, _ = journal_ordered(load_journal(target, effort))
            journal_open = open_items
        efforts.append(EffortView(
            effort=effort,
            goal=record_payload(goal).get("goal", ""),
            phases=phase_rows,
            milestones=milestone_rows,
            tasks=_task_rows(
                effort_tasks,
                listed["conductor:assignment"],
                listed["conductor:assignment-amendment"],
                listed["conductor:execution-report"],
                effort_checks,
                phases.get(effort, []),
            ),
            needs_you=_needs_you(
                questions.get(effort, []), findings.get(effort, []), effort_checks, acceptances_by_id,
                effort_tasks, assessments_by_effort.get(effort, []), integrations_by_effort.get(effort, []),
                {phase for spec_effort, phase in structured if spec_effort == effort},
            ),
            activity=activity.get(effort, []),
            release_ready=any(row.evidence is not None and row.evidence.release_ready for row in phase_rows),
            position=positions.get(effort, ""),
            kind=kind,
            journal_open=journal_open,
            backlog=_backlog_items(backlog_by_effort.get(effort, [])),
            area=areas.get(effort, ""),
        ))
    efforts.sort(key=lambda view: view.finished)
    return Snapshot(efforts, token, now)
