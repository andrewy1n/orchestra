"""Dashboard snapshot built from canon records, one list per record type."""

from __future__ import annotations

from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone

from dashboard.backend import store
from dashboard.backend.journal import JournalItem, load_journal
from dashboard.backend.journal import ordered as journal_ordered
from dashboard.backend.phase import (
    LIVE_PHASE_STATES,
    MilestoneRow,
    PhaseEvidence,
    PhaseRow,
    attach_milestones,
    current_phase_models,
    evidence_records_by_phase,
    phase_evidence,
)
from dashboard.backend.phase import (
    milestone_rows as build_milestone_rows,
)
from dashboard.backend.phase import (
    phase_rows as build_phase_rows,
)
from dashboard.backend.records import (
    CHECK_RESULT,
    INACTIVE_STATES,
    list_records,
    live_records,
    recorded_at,
    records_by_effort,
)
from dashboard.backend.stages import load_phase_progress
from dashboard.backend.store import change_token
from dashboard.backend.task import (
    TaskRow,
    configured_small_wave_budget,
    task_rows,
)
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.composer.records import IDEA, current_placements, read_idea
from orchestra.conductor.attention import LandingFact, attention_items
from orchestra.conductor.effort_status import EffortStatus, effort_statuses
from orchestra.conductor.model_types import planning_payload as record_payload
from orchestra.derive import phase_progress
from orchestra.score.lookups import LIVE_WORK_ITEM_STATES, owning_work_item

RECENT = timedelta(hours=24)
NEEDS_ORDER = (
    "blocking-question",
    "loop-route",
    "integration",
    "merge-branch",
    "needs-human",
    "unsigned-check",
    "open-question",
)
FULL_TYPES = (
    "score:continuity-question",
    "tuner:finding",
    "tuner:check-run",
    "score:work-item",
    "score:phase",
    "score:specification",
    "conductor:assessment",
    "conductor:integration-report",
    "conductor:proof-packet",
    "composer:idea",
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
    updated_at: datetime | None = None


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
    updated_at: datetime | None = None


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
    journal_open: list[JournalItem] = field(default_factory=list)
    backlog: list[BacklogItem] = field(default_factory=list)
    area: str = ""
    status: EffortStatus = "live"

    @property
    def finished(self) -> bool:
        return self.status == "finished"

    @property
    def dormant(self) -> bool:
        return self.status == "dormant"


@dataclass
class Snapshot:
    efforts: list[EffortView]
    token: str
    generated_at: datetime


_SNAPSHOT_TYPES = (
    "score:effort",
    "score:phase",
    "score:milestone",
    "score:work-item",
    "score:continuity-question",
    "tuner:finding",
    "tuner:check-run",
    "conductor:assignment",
    "conductor:assignment-amendment",
    "conductor:execution-report",
    "score:specification",
    "score:design",
    "conductor:assessment",
    "conductor:integration-report",
    "conductor:release",
    "score:position",
    "composer:idea",
    PLACEMENT_TYPE,
)


def _list_all(
    target: Project, record_types: tuple[str, ...], token: str
) -> dict[str, list[Record]]:
    def load(record_type: str) -> list[Record]:
        with store.pinned_token(token):
            return list_records(target, record_type)

    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(zip(record_types, pool.map(load, record_types), strict=False))


def _structured_phases(specs: list[Record]) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for record in live_records(specs):
        payload = record_payload(record)
        effort, phase = payload.get("effort") or "", payload.get("phase") or ""
        if effort and phase:
            found.add((effort, phase))
    return found


def _light_phases(phase_records: list[Record]) -> set[tuple[str, str]]:
    return {
        (phase.effort, phase.subject)
        for phase in current_phase_models(phase_records)
        if phase.weight == "light"
    }


def _assessment_summary(record: Record, by_id: dict[str, Record]) -> tuple[str, bool]:
    payload = record_payload(record)
    summary = (
        f"{payload.get('requirement', '')} {payload.get('status', '')} {payload.get('next', '')}"
    )
    if payload.get("next") in UPSTREAM_NEXT:
        summary += " upstream"
    links = (record.get("relationships") or {}).get("supersedes") or []
    previous = by_id.get(links[0]) if links else None
    if previous is not None:
        old, new = record_payload(previous).get("level") or "", payload.get("level") or ""
        if old != new:
            summary += f" level {old} to {new}"
    return summary, payload.get("status") in ("failed", "blocked")


def _live(tasks: list[Record]) -> list[Record]:
    return [task for task in tasks if task["lifecycle_state"] in LIVE_WORK_ITEM_STATES]


def _task_for(subject: str, tasks: list[Record]) -> str:
    owner = owning_work_item(subject, _live(tasks))
    return owner["id"] if owner else ""


def _backlog_items(records: list[Record]) -> list[BacklogItem]:
    items: list[BacklogItem] = []
    for record in records:
        if record.get("lifecycle_state") in INACTIVE_STATES:
            continue
        idea = read_idea(record)
        if idea.status != "open":
            continue
        items.append(
            BacklogItem(
                id=record["id"],
                subject=idea.subject,
                effort=idea.effort,
                text=idea.text,
                status=idea.status,
                source=idea.source,
                phase=idea.phase,
                body=record.get("body") or "",
                record_type=record.get("record_type") or IDEA,
                updated_at=recorded_at(record),
            )
        )
    items.sort(key=lambda item: (item.subject, item.id))
    return items


def _earliest_by_subject(items: list[tuple[int, Record]]) -> dict[str, tuple[int, Record]]:
    found: dict[str, tuple[int, Record]] = {}
    for index, record in items:
        current = found.get(record["subject"])
        if current is None or index < current[0]:
            found[record["subject"]] = (index, record)
    return found


def _prefixed_owner(
    subject: str, owners: dict[str, tuple[int, Record]]
) -> tuple[int, Record] | None:
    parts = subject.split("-")
    for count in range(len(parts), 0, -1):
        found = owners.get("-".join(parts[:count]))
        if found is not None:
            return found
    return None


def _effort_matches(check: Record, task: Record) -> bool:
    effort = record_payload(task).get("effort", "")
    return record_payload(check).get("effort", effort) == effort


def _owns_against_live(
    index: int, task: Record, subject: str, live: tuple[int, Record] | None
) -> bool:
    name = task["subject"]
    if subject != name and not subject.startswith(f"{name}-"):
        return False
    if live is None:
        return True
    live_index, live_task = live
    length = len(name)
    live_length = len(live_task["subject"])
    return length > live_length or (length == live_length and index < live_index)


def _check_stamps(
    phase: str, members: list[Record], tasks: list[Record], checks: list[Record]
) -> list[datetime]:
    member_ids = {task["id"] for task in members}
    live: list[tuple[int, Record]] = []
    other: list[tuple[int, Record]] = []
    for index, task in enumerate(tasks):
        if (
            task["lifecycle_state"] in LIVE_WORK_ITEM_STATES
            and record_payload(task).get("phase") == phase
        ):
            live.append((index, task))
        elif task["id"] in member_ids:
            other.append((index, task))
    owners = _earliest_by_subject(live)
    stamps: list[datetime] = []
    for check in checks:
        subject = check["subject"]
        winner = _prefixed_owner(subject, owners)
        if winner is not None and _effort_matches(check, winner[1]):
            stamps.append(recorded_at(check))
            continue
        for index, task in other:
            if _owns_against_live(index, task, subject, winner) and _effort_matches(check, task):
                stamps.append(recorded_at(check))
                break
    return stamps


def _max_check_stamp_by_phase(tasks: list[Record], checks: list[Record]) -> dict[str, datetime]:
    live_by_phase: dict[str, list[tuple[int, Record]]] = {}
    other_by_subject: dict[str, list[tuple[str, int, Record]]] = {}
    for index, task in enumerate(tasks):
        phase_name = record_payload(task).get("phase")
        if not isinstance(phase_name, str):
            continue
        if task["lifecycle_state"] in LIVE_WORK_ITEM_STATES:
            live_by_phase.setdefault(phase_name, []).append((index, task))
        else:
            other_by_subject.setdefault(task["subject"], []).append((phase_name, index, task))
    by_subject: dict[str, list[tuple[str, int, Record]]] = {}
    for phase_name, items in live_by_phase.items():
        for subject, (index, record) in _earliest_by_subject(items).items():
            by_subject.setdefault(subject, []).append((phase_name, index, record))
    stamps: dict[str, datetime] = {}

    def consider(phase_name: str, stamp: datetime) -> None:
        current = stamps.get(phase_name)
        if current is None or stamp > current:
            stamps[phase_name] = stamp

    for check in checks:
        subject = check["subject"]
        parts = subject.split("-")
        live_best: dict[str, tuple[int, int, Record]] = {}
        for count in range(len(parts), 0, -1):
            name = "-".join(parts[:count])
            hits = by_subject.get(name)
            if not hits:
                continue
            length = len(name)
            for phase_name, index, record in hits:
                current = live_best.get(phase_name)
                if (
                    current is None
                    or length > current[0]
                    or (length == current[0] and index < current[1])
                ):
                    live_best[phase_name] = (length, index, record)
        stamp = recorded_at(check)
        matched: set[str] = set()
        for phase_name, (_length, _index, record) in live_best.items():
            if _effort_matches(check, record):
                consider(phase_name, stamp)
                matched.add(phase_name)
        for count in range(len(parts), 0, -1):
            name = "-".join(parts[:count])
            hits = other_by_subject.get(name)
            if not hits:
                continue
            for phase_name, index, record in hits:
                if phase_name in matched:
                    continue
                live = live_best.get(phase_name)
                live_pair = None if live is None else (live[1], live[2])
                if _owns_against_live(index, record, subject, live_pair) and _effort_matches(
                    check, record
                ):
                    consider(phase_name, stamp)
                    matched.add(phase_name)
    return stamps


def _work_item_stamps(records: list[Record]) -> dict[str, datetime]:
    stamps: dict[str, datetime] = {}
    for record in records:
        work_item = record_payload(record).get("work_item")
        if not isinstance(work_item, str) or not work_item:
            continue
        stamp = recorded_at(record)
        current = stamps.get(work_item)
        if current is None or stamp > current:
            stamps[work_item] = stamp
    return stamps


def _phase_updated_at(
    row: PhaseRow,
    phase_records: list[Record],
    tasks: list[Record],
    assignments: list[Record],
    reports: list[Record],
    checks: list[Record],
    check_stamps: dict[str, datetime] | None = None,
    work_stamps: dict[str, datetime] | None = None,
) -> datetime | None:
    members = [task for task in tasks if record_payload(task).get("phase") == row.subject]
    names = {task["id"] for task in members} | {task["subject"] for task in members}
    stamps = [recorded_at(record) for record in phase_records if record["id"] == row.id]
    stamps.extend(recorded_at(task) for task in members)
    if work_stamps is None:
        for record in (*assignments, *reports):
            if record_payload(record).get("work_item") in names:
                stamps.append(recorded_at(record))
    else:
        for name in names:
            stamp = work_stamps.get(name)
            if stamp is not None:
                stamps.append(stamp)
    if check_stamps is None:
        stamps.extend(_check_stamps(row.subject, members, tasks, checks))
    else:
        stamp = check_stamps.get(row.subject)
        if stamp is not None:
            stamps.append(stamp)
    return max(stamps, default=None)


def _needs_you(
    records: list[Record],
    effort: str,
    tasks: list[Record],
    landing: Mapping[str, LandingFact],
) -> list[NeedsYouItem]:
    return [
        NeedsYouItem(
            item.kind,
            item.record_id,
            item.subject,
            item.text,
            record_type=item.record_type,
            body=item.body,
            task_id="" if item.kind == "merge-branch" else _task_for(item.subject, tasks),
            phase=item.phase,
            requirement=item.requirement,
            status=item.status,
            next=item.next,
            result=item.result,
            revision=item.revision,
            updated_at=item.updated_at,
        )
        for item in attention_items(records, effort, landing)
    ]


def _activity(
    assignments: list[Record],
    reports: list[Record],
    checks: list[Record],
    efforts_by_work_item: dict[str, tuple[str, str]],
    since: datetime,
    assessments: list[Record] | None = None,
    integrations: list[Record] | None = None,
    releases: list[Record] | None = None,
    structured: set[tuple[str, str]] | None = None,
) -> dict[str, list[ActivityItem]]:
    by_effort: dict[str, list[ActivityItem]] = {}

    def add(
        effort: str | None, kind: str, record: Record, summary: str, failed: bool = False
    ) -> None:
        if effort is not None and recorded_at(record) >= since:
            by_effort.setdefault(effort, []).append(
                ActivityItem(
                    kind, record["id"], record["subject"], recorded_at(record), summary, failed
                )
            )

    def work_item(record: Record) -> tuple[str | None, str]:
        ref = record_payload(record).get("work_item", "")
        effort, subject = efforts_by_work_item.get(ref, (None, ref))
        return effort, subject

    for record in assignments:
        effort, subject = work_item(record)
        add(
            record_payload(record).get("effort") or effort,
            "assignment",
            record,
            f"{subject} assigned to {record_payload(record).get('executor', '')}",
        )
    for record in reports:
        effort, subject = work_item(record)
        payload = record_payload(record)
        add(
            effort,
            "execution-report",
            record,
            f"{subject} reported {payload.get('verdict', '')}",
            "fail" in (payload.get("result"), payload.get("verdict")),
        )
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
        add(
            payload.get("effort"),
            "integration",
            record,
            f"{payload.get('phase', '')} {result}",
            result in ("fail", "blocked"),
        )
    for record in releases or []:
        payload = record_payload(record)
        if (payload.get("effort"), payload.get("phase")) not in structured:
            continue
        state = payload.get("state", "")
        add(
            payload.get("effort"),
            "release",
            record,
            f"{payload.get('phase', '')} {state}",
            state == "failed",
        )
    for items in by_effort.values():
        items.sort(key=lambda item: item.recorded_at, reverse=True)
    return by_effort


def load_snapshot(
    target: Project,
    now: datetime | None = None,
    token: str | None = None,
    landing: Mapping[str, LandingFact] | None = None,
) -> Snapshot:
    token = token or change_token(target)
    with store.pinned_token(token):
        return _load_snapshot(target, now or datetime.now(timezone.utc), token, landing or {})


def _load_snapshot(
    target: Project, now: datetime, token: str, landing: Mapping[str, LandingFact]
) -> Snapshot:
    progress = load_phase_progress(target, token)
    listed = _list_all(target, _SNAPSHOT_TYPES, token)
    small_wave_budget_minutes = configured_small_wave_budget(target, listed["score:work-item"])
    goals = [
        r
        for r in listed["score:effort"]
        if r["lifecycle_state"] == "active" and record_payload(r).get("status") != "closed"
    ]
    phases = records_by_effort(listed["score:phase"])
    milestones = records_by_effort(listed.get("score:milestone") or [])
    all_tasks = listed["score:work-item"]
    tasks = records_by_effort(all_tasks)
    checks_all = listed["tuner:check-run"]
    checks = records_by_effort(checks_all)
    acceptances_all = list_records(target, "score:acceptance")
    acceptances = records_by_effort(acceptances_all)
    efforts_by_work_item: dict[str, tuple[str, str]] = {}
    for task in all_tasks:
        entry = (record_payload(task).get("effort") or "", task["subject"])
        efforts_by_work_item[task["id"]] = entry
        efforts_by_work_item.setdefault(task["subject"], entry)
    specs = listed["score:specification"]
    designs = listed["score:design"]
    assessments = listed["conductor:assessment"]
    integrations = listed["conductor:integration-report"]
    releases = listed["conductor:release"]
    backlog_by_effort = records_by_effort(listed.get("composer:idea") or [])
    decisions = list_records(target, "score:decision") if designs else []
    structured = _structured_phases(specs) | _light_phases(listed["score:phase"])
    specs_by_effort = records_by_effort(specs)
    designs_by_effort = records_by_effort(designs)
    assessments_by_effort = records_by_effort(assessments)
    integrations_by_effort = records_by_effort(integrations)
    releases_by_effort = records_by_effort(releases)
    decisions_by_effort = records_by_effort(decisions)
    activity = _activity(
        listed["conductor:assignment"],
        listed["conductor:execution-report"],
        checks_all,
        efforts_by_work_item,
        now - RECENT,
        assessments,
        integrations,
        releases,
        structured,
    )
    positions = {
        record["subject"]: record_payload(record).get("position", "")
        for record in listed["score:position"]
        if record["lifecycle_state"] == "active"
        and record_payload(record).get("status") != "closed"
        and record_payload(record).get("scope") == "effort"
    }
    areas = current_placements(live_records(listed[PLACEMENT_TYPE]))
    every_record = store.catalog_records(target)
    status_by_effort = effort_statuses(every_record, now)
    work_stamps = _work_item_stamps(
        [*listed["conductor:assignment"], *listed["conductor:execution-report"]]
    )
    efforts: list[EffortView] = []
    for goal in sorted(goals, key=lambda record: record["subject"]):
        effort = goal["subject"]
        effort_tasks = tasks.get(effort, [])
        effort_acceptances = acceptances.get(effort, [])
        effort_checks = checks.get(effort, [])
        phase_acceptances, phase_checks = evidence_records_by_phase(
            effort_acceptances, effort_checks
        )
        evidence_by_phase: dict[str, PhaseEvidence] = {}
        for spec_effort, phase in structured:
            if spec_effort != effort:
                continue
            evidence = phase_evidence(
                phase,
                effort,
                specs_by_effort.get(effort, []),
                designs_by_effort.get(effort, []),
                decisions_by_effort.get(effort, []),
                effort_tasks,
                phase_acceptances.get(phase, []),
                phase_checks.get(phase, []),
                assessments_by_effort.get(effort, []),
                integrations_by_effort.get(effort, []),
                releases_by_effort.get(effort, []),
                phases.get(effort, []),
                progress.get(phase),
            )
            if evidence is not None:
                evidence_by_phase[phase] = evidence
        phase_rows = build_phase_rows(
            phases.get(effort, []),
            effort_tasks,
            effort_acceptances,
            effort_checks,
            evidence_by_phase,
            small_wave_budget_minutes=small_wave_budget_minutes,
        )
        check_stamps = _max_check_stamp_by_phase(effort_tasks, effort_checks)
        phase_rows = [
            replace(
                row,
                progress=progress.get(row.subject),
                updated_at=_phase_updated_at(
                    row,
                    phases.get(effort, []),
                    effort_tasks,
                    listed["conductor:assignment"],
                    listed["conductor:execution-report"],
                    effort_checks,
                    check_stamps,
                    work_stamps,
                ),
            )
            for row in phase_rows
        ]
        effort_milestones = build_milestone_rows(milestones.get(effort, []), phase_rows)
        phase_rows = attach_milestones(phase_rows, effort_milestones)
        kind = record_payload(goal).get("kind") or ""
        journal_open = []
        if kind in ("repair", "evaluate"):
            open_items, _ = journal_ordered(load_journal(target, effort))
            journal_open = open_items
        efforts.append(
            EffortView(
                effort=effort,
                goal=record_payload(goal).get("goal", ""),
                phases=phase_rows,
                milestones=effort_milestones,
                tasks=task_rows(
                    effort_tasks,
                    listed["conductor:assignment"],
                    listed["conductor:assignment-amendment"],
                    listed["conductor:execution-report"],
                    effort_checks,
                    phases.get(effort, []),
                    small_wave_budget_minutes=small_wave_budget_minutes,
                ),
                needs_you=_needs_you(every_record, effort, effort_tasks, landing),
                activity=activity.get(effort, []),
                release_ready=any(
                    row.evidence is not None and row.evidence.release_ready for row in phase_rows
                ),
                position=positions.get(effort, ""),
                kind=kind,
                journal_open=journal_open,
                backlog=_backlog_items(backlog_by_effort.get(effort, [])),
                area=areas.get(effort, ""),
                status=status_by_effort.get(effort, "live"),
            )
        )
    efforts.sort(key=lambda view: view.finished)
    return Snapshot(efforts, token, now)


_WORK_TYPES = (
    "score:effort",
    "score:phase",
    "score:work-item",
    "score:acceptance",
    "score:continuity-question",
    "score:specification",
    "score:design",
    "tuner:finding",
    "tuner:check-run",
    "conductor:assignment",
    "conductor:execution-report",
    "conductor:assessment",
    "conductor:integration-report",
    "conductor:release",
    "composer:idea",
)


def load_work_snapshot(
    target: Project, now: datetime | None = None, token: str | None = None
) -> Snapshot:
    target = replace(target, read_only=True)
    now = now or datetime.now(timezone.utc)
    token = token or change_token(target)
    progress = load_phase_progress(target, token)
    with store.pinned_token(token):
        every_record = store.catalog_records(target)
    listed: dict[str, list[Record]] = {record_type: [] for record_type in _WORK_TYPES}
    for record in every_record:
        type_records = listed.get(record["record_type"])
        if type_records is not None:
            type_records.append(record)
    small_wave_budget_minutes = configured_small_wave_budget(target, listed["score:work-item"])
    grouped = {record_type: records_by_effort(rows) for record_type, rows in listed.items()}
    structured = _structured_phases(listed["score:specification"]) | _light_phases(
        listed["score:phase"]
    )
    goals = [
        record
        for record in listed["score:effort"]
        if record["lifecycle_state"] == "active"
        and record_payload(record).get("status") != "closed"
    ]
    status_by_effort = effort_statuses(every_record, now)
    work_stamps = _work_item_stamps(
        [*listed["conductor:assignment"], *listed["conductor:execution-report"]]
    )
    efforts: list[EffortView] = []
    for goal in sorted(goals, key=lambda record: record["subject"]):
        effort = goal["subject"]
        phase_models = [
            phase
            for phase in current_phase_models(grouped["score:phase"].get(effort, []))
            if phase.record["lifecycle_state"] in LIVE_PHASE_STATES
        ]
        phases = [phase.record for phase in phase_models]
        tasks = grouped["score:work-item"].get(effort, [])
        if status_by_effort.get(effort, "live") in ("finished", "dormant"):
            continue
        acceptances = grouped["score:acceptance"].get(effort, [])
        checks = grouped["tuner:check-run"].get(effort, [])
        assessments = grouped["conductor:assessment"].get(effort, [])
        integrations = grouped["conductor:integration-report"].get(effort, [])
        phase_acceptances, phase_checks = evidence_records_by_phase(acceptances, checks)
        active_subjects = {
            record["subject"] for record in phases if record["lifecycle_state"] == "in_progress"
        }
        active_tasks = [
            task for task in tasks if record_payload(task).get("phase") in active_subjects
        ]
        check_stamps = _max_check_stamp_by_phase(tasks, checks)
        rows: list[PhaseRow] = []
        for current in phase_models:
            if current.record["lifecycle_state"] != "in_progress":
                continue
            phase = current.subject
            counts = phase_progress(tasks, phase)
            evidence = None
            if (effort, phase) in structured:
                evidence = phase_evidence(
                    phase,
                    effort,
                    grouped["score:specification"].get(effort, []),
                    grouped["score:design"].get(effort, []),
                    [],
                    tasks,
                    phase_acceptances.get(phase, []),
                    phase_checks.get(phase, []),
                    assessments,
                    integrations,
                    grouped["conductor:release"].get(effort, []),
                    phases,
                    progress.get(phase),
                )
            row = PhaseRow(
                subject=phase,
                title=current.title,
                ordinal=current.ordinal,
                state=current.record["lifecycle_state"],
                done=counts.done,
                total=counts.total,
                id=current.id,
                evidence=evidence,
                body=current.body,
                in_progress=counts.in_progress,
                progress=progress.get(phase),
            )
            rows.append(
                replace(
                    row,
                    updated_at=_phase_updated_at(
                        row,
                        phases,
                        tasks,
                        listed["conductor:assignment"],
                        listed["conductor:execution-report"],
                        checks,
                        check_stamps,
                        work_stamps,
                    ),
                )
            )
        rows.sort(key=lambda row: (row.ordinal, row.subject))
        efforts.append(
            EffortView(
                effort=effort,
                goal=record_payload(goal).get("goal", ""),
                phases=rows,
                tasks=task_rows(
                    active_tasks,
                    small_wave_budget_minutes=small_wave_budget_minutes,
                ),
                needs_you=_needs_you(every_record, effort, tasks, {}),
                backlog=_backlog_items(grouped["composer:idea"].get(effort, [])),
            )
        )
    return Snapshot(efforts, token, now)
