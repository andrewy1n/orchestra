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
    list_records,
    live_records,
    recorded_at,
    records_by_effort,
)
from dashboard.backend.stages import load_phase_progress
from dashboard.backend.store import change_token
from dashboard.backend.task import (
    TaskRow,
    configured_executor_settings,
    task_rows,
)
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.composer.records import IDEA, PLACEMENT, current_placements, open_ideas
from orchestra.conductor.landing.landing import PROOF_PACKET
from orchestra.conductor.model_types import planning_payload as record_payload
from orchestra.conductor.phases.progress.activity import activity_entries
from orchestra.conductor.phases.progress.attention import LandingFact, attention_items
from orchestra.conductor.phases.progress.effort_status import EffortStatus, effort_statuses
from orchestra.conductor.phases.progress.phase_progress import phase_counts
from orchestra.conductor.tasks.assignment import ASSIGNMENT
from orchestra.conductor.tasks.task_detail import (
    ASSIGNMENT_AMENDMENT_TYPE,
    EXECUTION_REPORT_TYPE,
)
from orchestra.conductor.workspace_types import (
    ASSESSMENT_TYPE,
    INTEGRATION_REPORT_TYPE,
    RELEASE_TYPE,
)
from orchestra.score.facts.detail_facts import (
    ACCEPTANCE_TYPE,
    DECISION_TYPE,
    PHASE_TYPE,
    WORK_ITEM_TYPE,
)
from orchestra.score.facts.work_item_facts import owning_task_id, record_scope
from orchestra.score.facts.workspace_facts import (
    CONTINUITY_QUESTION_TYPE,
    DESIGN_TYPE,
    MILESTONE_TYPE,
    POSITION_TYPE,
    effort_positions,
    effort_summary,
    work_item_efforts,
)
from orchestra.score.lookups import LIVE_WORK_ITEM_STATES
from orchestra.score.planning.effort import EFFORT, current_efforts
from orchestra.score.planning.phase import structured_phases
from orchestra.score.planning.requirements import SPECIFICATION
from orchestra.tuner.evidence.evidence_facts import CHECK_RUN_TYPE, FINDING_TYPE

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
    CONTINUITY_QUESTION_TYPE,
    FINDING_TYPE,
    CHECK_RUN_TYPE,
    WORK_ITEM_TYPE,
    PHASE_TYPE,
    SPECIFICATION,
    ASSESSMENT_TYPE,
    INTEGRATION_REPORT_TYPE,
    PROOF_PACKET,
    IDEA,
)


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
    record_type: str = IDEA
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
    status: EffortStatus
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
    EFFORT,
    PHASE_TYPE,
    MILESTONE_TYPE,
    WORK_ITEM_TYPE,
    CONTINUITY_QUESTION_TYPE,
    FINDING_TYPE,
    CHECK_RUN_TYPE,
    ASSIGNMENT,
    ASSIGNMENT_AMENDMENT_TYPE,
    EXECUTION_REPORT_TYPE,
    SPECIFICATION,
    DESIGN_TYPE,
    ASSESSMENT_TYPE,
    INTEGRATION_REPORT_TYPE,
    RELEASE_TYPE,
    POSITION_TYPE,
    IDEA,
    PLACEMENT,
)


def _list_all(
    target: Project, record_types: tuple[str, ...], token: str
) -> dict[str, list[Record]]:
    view = store.pinned_catalog()

    def load(record_type: str) -> list[Record]:
        with store.pinned(view) if view is not None else store.pinned_token(token):
            return list_records(target, record_type)

    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(zip(record_types, pool.map(load, record_types), strict=False))


def _backlog_items(records: list[Record]) -> list[BacklogItem]:
    return [
        BacklogItem(
            id=idea.record["id"],
            subject=idea.subject,
            effort=idea.effort,
            text=idea.text,
            status=idea.status,
            source=idea.source,
            phase=idea.phase,
            body=idea.record.get("body") or "",
            record_type=idea.record.get("record_type") or IDEA,
            updated_at=recorded_at(idea.record),
        )
        for idea in open_ideas(records)
    ]


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
            task_id="" if item.kind == "merge-branch" else owning_task_id(item.subject, tasks),
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
    entries = activity_entries(
        assignments,
        reports,
        checks,
        efforts_by_work_item,
        since,
        assessments,
        integrations,
        releases,
        structured,
    )
    return {
        effort: [
            ActivityItem(
                item.kind, item.id, item.subject, item.recorded_at, item.summary, item.failed
            )
            for item in items
        ]
        for effort, items in entries.items()
    }


def load_snapshot(
    target: Project,
    now: datetime | None = None,
    token: str | None = None,
    landing: Mapping[str, LandingFact] | None = None,
) -> Snapshot:
    token = token or change_token(target)
    with store.pinned_token(token):
        return _load_snapshot(target, now or datetime.now(timezone.utc), token, landing or {})


def with_landing(
    target: Project, snapshot: Snapshot, landing: Mapping[str, LandingFact]
) -> Snapshot:
    """Return the snapshot with each effort's Needs you list rebuilt from the landing facts."""
    with store.pinned_token(snapshot.token):
        every_record = store.catalog_records(target)
        tasks = records_by_effort(list_records(target, WORK_ITEM_TYPE))
    return replace(
        snapshot,
        efforts=[
            replace(
                view,
                needs_you=_needs_you(
                    every_record, view.effort, tasks.get(view.effort, []), landing
                ),
            )
            for view in snapshot.efforts
        ],
    )


def _load_snapshot(
    target: Project, now: datetime, token: str, landing: Mapping[str, LandingFact]
) -> Snapshot:
    progress = load_phase_progress(target, token)
    listed = _list_all(target, _SNAPSHOT_TYPES, token)
    settings = configured_executor_settings(target, listed[WORK_ITEM_TYPE])
    goals = [
        effort.record
        for effort in current_efforts(listed[EFFORT]).values()
        if effort.status != "closed"
    ]
    phases = records_by_effort(listed[PHASE_TYPE])
    milestones = records_by_effort(listed.get(MILESTONE_TYPE) or [])
    all_tasks = listed[WORK_ITEM_TYPE]
    tasks = records_by_effort(all_tasks)
    checks_all = listed[CHECK_RUN_TYPE]
    checks = records_by_effort(checks_all)
    acceptances_all = list_records(target, ACCEPTANCE_TYPE)
    acceptances = records_by_effort(acceptances_all)
    efforts_by_work_item = work_item_efforts(all_tasks)
    specs = listed[SPECIFICATION]
    designs = listed[DESIGN_TYPE]
    assessments = listed[ASSESSMENT_TYPE]
    integrations = listed[INTEGRATION_REPORT_TYPE]
    releases = listed[RELEASE_TYPE]
    backlog_by_effort = records_by_effort(listed.get(IDEA) or [])
    decisions = list_records(target, DECISION_TYPE) if designs else []
    structured = structured_phases(specs, listed[PHASE_TYPE])
    specs_by_effort = records_by_effort(specs)
    designs_by_effort = records_by_effort(designs)
    assessments_by_effort = records_by_effort(assessments)
    integrations_by_effort = records_by_effort(integrations)
    releases_by_effort = records_by_effort(releases)
    decisions_by_effort = records_by_effort(decisions)
    activity = _activity(
        listed[ASSIGNMENT],
        listed[EXECUTION_REPORT_TYPE],
        checks_all,
        efforts_by_work_item,
        now - RECENT,
        assessments,
        integrations,
        releases,
        structured,
    )
    positions = effort_positions(listed[POSITION_TYPE])
    areas = current_placements(live_records(listed[PLACEMENT]))
    every_record = store.catalog_records(target)
    status_by_effort = effort_statuses(every_record, now)
    work_stamps = _work_item_stamps([*listed[ASSIGNMENT], *listed[EXECUTION_REPORT_TYPE]])
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
            settings=settings,
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
                    listed[ASSIGNMENT],
                    listed[EXECUTION_REPORT_TYPE],
                    effort_checks,
                    check_stamps,
                    work_stamps,
                ),
            )
            for row in phase_rows
        ]
        effort_milestones = build_milestone_rows(milestones.get(effort, []), phase_rows)
        phase_rows = attach_milestones(phase_rows, effort_milestones)
        summary = effort_summary(goal)
        kind = summary.kind
        journal_open = []
        if kind in ("repair", "evaluate"):
            open_items, _ = journal_ordered(load_journal(target, effort))
            journal_open = open_items
        efforts.append(
            EffortView(
                effort=effort,
                goal=summary.goal,
                phases=phase_rows,
                milestones=effort_milestones,
                tasks=task_rows(
                    effort_tasks,
                    listed[ASSIGNMENT],
                    listed[ASSIGNMENT_AMENDMENT_TYPE],
                    listed[EXECUTION_REPORT_TYPE],
                    effort_checks,
                    phases.get(effort, []),
                    settings=settings,
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
                status=status_by_effort[effort],
            )
        )
    efforts.sort(key=lambda view: view.finished)
    return Snapshot(efforts, token, now)


_WORK_TYPES = (
    EFFORT,
    PHASE_TYPE,
    WORK_ITEM_TYPE,
    ACCEPTANCE_TYPE,
    CONTINUITY_QUESTION_TYPE,
    SPECIFICATION,
    DESIGN_TYPE,
    FINDING_TYPE,
    CHECK_RUN_TYPE,
    ASSIGNMENT,
    EXECUTION_REPORT_TYPE,
    ASSESSMENT_TYPE,
    INTEGRATION_REPORT_TYPE,
    RELEASE_TYPE,
    IDEA,
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
    settings = configured_executor_settings(target, listed[WORK_ITEM_TYPE])
    grouped = {record_type: records_by_effort(rows) for record_type, rows in listed.items()}
    structured = structured_phases(listed[SPECIFICATION], listed[PHASE_TYPE])
    goals = [
        effort.record
        for effort in current_efforts(listed[EFFORT]).values()
        if effort.status != "closed"
    ]
    status_by_effort = effort_statuses(every_record, now)
    work_stamps = _work_item_stamps([*listed[ASSIGNMENT], *listed[EXECUTION_REPORT_TYPE]])
    efforts: list[EffortView] = []
    for goal in sorted(goals, key=lambda record: record["subject"]):
        effort = goal["subject"]
        phase_models = [
            phase
            for phase in current_phase_models(grouped[PHASE_TYPE].get(effort, []))
            if phase.record["lifecycle_state"] in LIVE_PHASE_STATES
        ]
        phases = [phase.record for phase in phase_models]
        tasks = grouped[WORK_ITEM_TYPE].get(effort, [])
        if status_by_effort[effort] in ("finished", "dormant"):
            continue
        acceptances = grouped[ACCEPTANCE_TYPE].get(effort, [])
        checks = grouped[CHECK_RUN_TYPE].get(effort, [])
        assessments = grouped[ASSESSMENT_TYPE].get(effort, [])
        integrations = grouped[INTEGRATION_REPORT_TYPE].get(effort, [])
        phase_acceptances, phase_checks = evidence_records_by_phase(acceptances, checks)
        active_subjects = {
            record["subject"] for record in phases if record["lifecycle_state"] == "in_progress"
        }
        active_tasks = [task for task in tasks if record_scope(task).phase in active_subjects]
        check_stamps = _max_check_stamp_by_phase(tasks, checks)
        rows: list[PhaseRow] = []
        for current in phase_models:
            if current.record["lifecycle_state"] != "in_progress":
                continue
            phase = current.subject
            counts = phase_counts(tasks, phase)
            evidence = None
            if (effort, phase) in structured:
                evidence = phase_evidence(
                    phase,
                    effort,
                    grouped[SPECIFICATION].get(effort, []),
                    grouped[DESIGN_TYPE].get(effort, []),
                    [],
                    tasks,
                    phase_acceptances.get(phase, []),
                    phase_checks.get(phase, []),
                    assessments,
                    integrations,
                    grouped[RELEASE_TYPE].get(effort, []),
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
                        listed[ASSIGNMENT],
                        listed[EXECUTION_REPORT_TYPE],
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
                goal=effort_summary(goal).goal,
                status=status_by_effort[effort],
                phases=rows,
                tasks=task_rows(
                    active_tasks,
                    settings=settings,
                ),
                needs_you=_needs_you(every_record, effort, tasks, {}),
                backlog=_backlog_items(grouped[IDEA].get(effort, [])),
            )
        )
    return Snapshot(efforts, token, now)
