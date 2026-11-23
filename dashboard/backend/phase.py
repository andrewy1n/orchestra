"""Phase rows, phase evidence, phase detail, decision log, and requirement detail."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from dashboard.backend.records import (
    INACTIVE_STATES,
    list_records,
    live_records,
    newest_record,
    recorded_at,
    records_by_effort,
)
from dashboard.backend.stages import load_phase_progress
from dashboard.backend.store import ModelError, current_token
from dashboard.backend.task import (
    DEFAULT_SMALL_WAVE_BUDGET_MINUTES,
    AcceptanceRow,
    CheckRun,
    RelatedRecord,
    TaskRow,
    check_from,
    configured_small_wave_budget,
    latest_checks,
    task_rows,
)
from orchestra.canon.project import Project
from orchestra.canon.sections import body_section_ci
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.assessment_facts import assessment_facts, latest_assessments
from orchestra.conductor.assignment import ASSIGNMENT
from orchestra.conductor.landing import PROOF_PACKET, proof_packet
from orchestra.conductor.phase_progress import PhaseProgress, phase_counts
from orchestra.conductor.release_facts import integration_result, is_release_ready, release_state
from orchestra.conductor.requirements import UNVERIFIED, RequirementStatus, requirement_status
from orchestra.conductor.signoff import awaiting_signoff
from orchestra.conductor.suite_label import suite_labels
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
from orchestra.score.facts.elapsed import TimedTask, phase_elapsed
from orchestra.score.facts.work_item_facts import (
    decision_choice,
    record_scope,
    tasks_by_requirement,
    work_item_facts,
)
from orchestra.score.facts.workspace_facts import (
    CONSTRAINT_TYPE,
    DESIGN_TYPE,
    MILESTONE_TYPE,
    constraint_facts,
    decision_facts,
)
from orchestra.score.lookups import (
    current_phases,
    live_work_items,
)
from orchestra.score.planning.acceptance import read_acceptance
from orchestra.score.planning.milestone import milestone_facts, milestone_state
from orchestra.score.planning.phase import Phase, current_phase_model, read_phase
from orchestra.score.planning.requirements import (
    SPECIFICATION,
    acceptance_listed_requirements,
    acceptance_requirement_ids,
    phase_requirements,
)
from orchestra.score.planning.scope import (
    design_decisions,
    records_for_phase,
    spec_requirements,
    spec_weight,
)
from orchestra.tuner.evidence.evidence_facts import CHECK_RUN_TYPE
from orchestra.tuner.evidence.record_facts import check_run_facts

LIVE_PHASE_STATES = ("planned", "in_progress", "done")


@dataclass(frozen=True)
class PhaseRow:
    subject: str
    title: str
    ordinal: int
    state: str
    done: int
    total: int
    id: str = ""
    awaiting_signoff: bool = False
    evidence: PhaseEvidence | None = None
    sitting: str = ""
    body: str = ""
    elapsed_minutes: int | None = None
    unset_estimates: int = 0
    suite: str = ""
    milestone: str = ""
    milestone_title: str = ""
    in_progress: tuple[str, ...] = ()
    updated_at: datetime | None = None
    progress: PhaseProgress | None = None


@dataclass(frozen=True)
class MilestoneRow:
    subject: str
    title: str
    ordinal: int
    state: str
    done: int
    total: int
    id: str = ""


def _texts_for(phases: list[Record], spec: Record | None, phase: str) -> dict[str, str]:
    return dict(phase_requirements([*phases, *([spec] if spec is not None else [])], phase))


def current_phase_models(records: list[Record]) -> list[Phase]:
    return [read_phase(record) for record in current_phases(records).values()]


def light_specification(phase: str, effort: str, phases: list[Record]) -> Record | None:
    current = current_phase_model(phase, phases)
    if current is None or current.weight != "light":
        return None
    record = current.record
    body = current.body
    payload: JsonObject = {
        "phase": phase,
        "effort": effort,
        "weight": "light",
        "requirements": [rid for rid, _ in phase_requirements(phases, phase)],
    }
    return {
        "id": record["id"],
        "record_type": SPECIFICATION,
        "subject": record["subject"],
        "payload": payload,
        "lifecycle_state": "active",
        "relationships": record["relationships"],
        "revision": record["revision"],
        "recorded_at": record["recorded_at"],
        "body": body,
    }


def _oldest_first(records: list[Record]) -> list[Record]:
    """Order a supersede chain from the original record to the active one.

    Supersede rewrites the predecessor's recorded_at to the moment it is retired,
    which is after the successor's recorded_at was chosen.
    """
    by_id = {record["id"]: record for record in records}
    previous: dict[str, str] = {}
    pointed: set[str] = set()
    for record in records:
        links = [
            ref
            for ref in (record.get("relationships") or {}).get("supersedes") or []
            if ref in by_id
        ]
        if links:
            previous[record["id"]] = links[0]
            pointed.add(links[0])
    ordered: list[Record] = []
    seen: set[str] = set()
    for start in sorted(
        (record for record in records if record["id"] not in pointed), key=recorded_at
    ):
        chain: list[Record] = []
        current: Record | None = start
        while current is not None and current["id"] not in seen:
            seen.add(current["id"])
            chain.append(current)
            current = by_id.get(previous.get(current["id"], ""))
        chain.reverse()
        ordered.extend(chain)
    ordered.extend(
        sorted((record for record in records if record["id"] not in seen), key=recorded_at)
    )
    return ordered


def _choice_text(record: Record) -> str:
    choice = decision_choice(record)
    return choice if isinstance(choice, str) else ""


def _choices(subjects: list[str], decisions: list[Record]) -> tuple[DecisionChoice, ...]:
    by_subject: dict[str, Record] = {}
    for record in sorted(live_records(decisions), key=recorded_at):
        by_subject[record["subject"]] = record
    return tuple(
        DecisionChoice(
            subject,
            _choice_text(by_subject[subject]) if subject in by_subject else "",
        )
        for subject in subjects
    )


def evidence_records_by_phase(
    acceptances: list[Record], checks: list[Record]
) -> tuple[dict[str, list[Record]], dict[str, list[Record]]]:
    by_phase: dict[str, list[Record]] = {}
    acceptance_phases: dict[str, str] = {}
    for record in acceptances:
        phase = record_scope(record).phase or ""
        by_phase.setdefault(phase, []).append(record)
        acceptance_phases[record["id"]] = phase
    phase_checks: dict[str, list[Record]] = {}
    for record in checks:
        phase = acceptance_phases.get(check_run_facts(record).criterion_id)
        if phase is not None:
            phase_checks.setdefault(phase, []).append(record)
    return by_phase, phase_checks


def sitting_phrase(body: str) -> str:
    """Return the phase sitting phrase from the first Size: line, or empty."""
    for line in (body or "").splitlines():
        if "Size:" not in line:
            continue
        text = line.split("Size:", 1)[1]
        if "more than one" in text:
            return "more than one"
        if "one sitting" in text:
            return "one sitting"
        return ""
    return ""


def phase_rows(
    records: list[Record],
    tasks: list[Record],
    acceptances: list[Record] | None = None,
    checks: list[Record] | None = None,
    evidence_by_phase: dict[str, PhaseEvidence] | None = None,
    *,
    small_wave_budget_minutes: int = DEFAULT_SMALL_WAVE_BUDGET_MINUTES,
) -> list[PhaseRow]:
    evidence_by_phase = evidence_by_phase or {}
    suite_runs = suite_labels(checks or [])
    rows: list[PhaseRow] = []
    for phase in current_phase_models(records):
        record = phase.record
        if record["lifecycle_state"] not in LIVE_PHASE_STATES:
            continue
        members = live_work_items(phase.subject, tasks)
        awaiting = awaiting_signoff(
            record["lifecycle_state"], members, tasks, acceptances or [], checks or []
        )
        elapsed = phase_elapsed(
            [
                TimedTask(row.id, row.wave, row.estimate_minutes, row.executor)
                for row in task_rows(members, small_wave_budget_minutes=small_wave_budget_minutes)
            ]
        )
        progress = phase_counts(members, phase.subject)
        body = phase.body
        rows.append(
            PhaseRow(
                subject=phase.subject,
                title=phase.title,
                ordinal=phase.ordinal,
                state=record["lifecycle_state"],
                done=progress.done,
                total=progress.total,
                id=phase.id,
                awaiting_signoff=awaiting,
                evidence=evidence_by_phase.get(phase.subject),
                sitting=sitting_phrase(body),
                body=body,
                elapsed_minutes=elapsed.minutes,
                unset_estimates=elapsed.unset_estimates,
                suite=suite_runs.label(phase.subject),
                milestone=phase.milestone or "",
                in_progress=progress.in_progress,
            )
        )
    rows.sort(key=lambda row: (row.ordinal, row.subject))
    return rows


def milestone_rows(records: list[Record], phases: list[PhaseRow]) -> list[MilestoneRow]:
    by_slug: dict[str, list[PhaseRow]] = {}
    for phase in phases:
        if phase.milestone:
            by_slug.setdefault(phase.milestone, []).append(phase)
    rows: list[MilestoneRow] = []
    for record in records:
        if record["lifecycle_state"] not in LIVE_PHASE_STATES:
            continue
        facts = milestone_facts(record)
        members = by_slug.get(facts.subject, [])
        rows.append(
            MilestoneRow(
                subject=facts.subject,
                title=facts.title,
                ordinal=facts.ordinal,
                state=milestone_state([phase.state for phase in members]),
                done=sum(phase.state == "done" for phase in members),
                total=len(members),
                id=facts.id,
            )
        )
    rows.sort(key=lambda row: (row.ordinal, row.subject))
    return rows


def attach_milestones(phases: list[PhaseRow], milestones: list[MilestoneRow]) -> list[PhaseRow]:
    """Copy milestone titles onto phases and sort ungrouped first, then by milestone ordinal."""
    from dataclasses import replace

    titles = {row.subject: row.title for row in milestones}
    ordinals = {row.subject: row.ordinal for row in milestones}
    attached = [
        replace(
            phase,
            milestone_title=titles.get(phase.milestone, "") if phase.milestone else "",
        )
        for phase in phases
    ]

    def sort_key(phase: PhaseRow) -> tuple[int, int, int, str]:
        if not phase.milestone:
            return (0, 0, phase.ordinal, phase.subject)
        return (1, ordinals.get(phase.milestone, 10**6), phase.ordinal, phase.subject)

    attached.sort(key=sort_key)
    return attached


@dataclass(frozen=True)
class DecisionChoice:
    subject: str
    choice: str


@dataclass(frozen=True)
class IntegrationView:
    result: str
    conflicts: str


@dataclass(frozen=True)
class RequirementRow:
    phase: str
    id: str
    text: str
    status: str
    next: str
    latest_check: CheckRun | None
    tasks: int
    tasks_done: int = 0
    confidence: str = ""
    check_kind: str = ""
    check_at: datetime | None = None


@dataclass(frozen=True)
class PhaseEvidence:
    phase: str
    weight: str
    requirements: tuple[RequirementRow, ...]
    stage: str
    integration: IntegrationView | None
    release_ready: bool
    decisions: tuple[DecisionChoice, ...]
    non_goals: str
    release_state: str = ""
    stage_reason: str = ""


@dataclass(frozen=True)
class AssessmentView:
    id: str
    status: str
    level: str
    next: str
    confidence: str


@dataclass(frozen=True)
class RequirementDetail:
    phase: str
    id: str
    text: str
    status: str
    next: str
    decisions: tuple[DecisionChoice, ...]
    tasks: tuple[TaskRow, ...]
    acceptances: tuple[AcceptanceRow, ...]
    assessments: tuple[AssessmentView, ...]


def _assessment_view(
    written: Record | None, derived: RequirementStatus | None
) -> tuple[str, str, str]:
    status = derived.status if derived is not None else UNVERIFIED
    if written is None:
        return status, "", ""
    facts = assessment_facts(written)
    nxt = facts.next if derived is not None and derived.assessment_id else ""
    return status, nxt, facts.confidence


def _live_pool(*groups: list[Record]) -> list[Record]:
    return [record for group in groups for record in live_records(group)]


def phase_evidence(
    phase: str,
    effort: str,
    specs: list[Record],
    designs: list[Record],
    decisions: list[Record],
    tasks: list[Record],
    acceptances: list[Record],
    checks: list[Record],
    assessments: list[Record],
    reports: list[Record],
    releases: list[Record],
    phases: list[Record] | None = None,
    progress: PhaseProgress | None = None,
) -> PhaseEvidence | None:
    spec = light_specification(phase, effort, phases or []) or newest_record(
        records_for_phase(specs, phase, effort)
    )
    if spec is None:
        return None
    spec_ids = spec_requirements(spec)
    texts = _texts_for(phases or [], spec, phase)
    latest = latest_assessments(assessments, phase)
    acceptances_by_phase, checks_by_phase = evidence_records_by_phase(acceptances, checks)
    acceptances = acceptances_by_phase.get(phase, [])
    checks = checks_by_phase.get(phase, [])
    live_acceptances = [
        record
        for record in acceptances
        if record.get("lifecycle_state") not in INACTIVE_STATES
        and record_scope(record).phase == phase
    ]
    acceptance_ids = {record["id"] for record in live_acceptances}
    requirements_by_acceptance = {
        record["id"]: set(listed)
        for record in live_acceptances
        if (listed := acceptance_listed_requirements(record)) is not None
    }
    checks_by_criterion: dict[str, list[Record]] = {}
    checks_by_requirement: dict[str, list[Record]] = {}
    for record in checks:
        if record.get("lifecycle_state") in INACTIVE_STATES:
            continue
        facts = check_run_facts(record)
        if facts.criterion_id not in acceptance_ids:
            continue
        checks_by_criterion.setdefault(facts.criterion_id, []).append(record)
        if facts.requirement:
            checks_by_requirement.setdefault(facts.requirement, []).append(record)
    traced_tasks = tasks_by_requirement(tasks, phase)
    pool = _live_pool([spec], acceptances, checks, assessments)
    derived = requirement_status(pool, phase)
    rows: list[RequirementRow] = []
    for requirement in spec_ids:
        status, nxt, confidence = _assessment_view(
            latest.get(requirement), derived.get(requirement)
        )
        traced = traced_tasks.get(requirement, [])
        matched: list[Record] = []
        for acceptance_id, names in requirements_by_acceptance.items():
            if requirement in names:
                matched.extend(checks_by_criterion.get(acceptance_id, ()))
        matched.extend(checks_by_requirement.get(requirement, ()))
        chosen = newest_record(matched)
        check = check_from(chosen) if chosen else None
        rows.append(
            RequirementRow(
                phase,
                requirement,
                texts.get(requirement, ""),
                status,
                nxt,
                check,
                len(traced),
                tasks_done=sum(1 for task in traced if task.get("lifecycle_state") == "done"),
                confidence=confidence,
                check_kind=check.evidence_kind if check else "",
                check_at=check.recorded_at if check else None,
            )
        )
    design = newest_record(records_for_phase(designs, phase, effort))
    subjects = list(design_decisions(design)) if design else []
    report = newest_record(records_for_phase(reports, phase, effort))
    integration = None
    if report is not None:
        integration = IntegrationView(
            integration_result(report),
            body_section_ci(report.get("body") or "", "Conflicts"),
        )
    latest_release = newest_record(records_for_phase(releases, phase, effort))
    release_ready = is_release_ready(latest_release, derived)
    release_state_text = release_state(latest_release) if latest_release else ""
    return PhaseEvidence(
        phase,
        spec_weight(spec),
        tuple(rows),
        (progress.current or "") if progress is not None else "",
        integration,
        release_ready,
        _choices(subjects, decisions),
        body_section_ci(spec.get("body") or "", "Non-goals"),
        release_state=release_state_text,
        stage_reason=progress.reason if progress is not None else "",
    )


TABS = ("overview", "spec", "design", "decisions", "evidence", "proof", "tasks")
SIMPLE_TABS = ("overview", "proof", "spec", "decisions", "tasks")


@dataclass(frozen=True)
class ProofView:
    id: str
    kind: str
    revision: str
    base: str
    look: str
    attention: str
    machine: str
    diff: str


@dataclass(frozen=True)
class DecisionEntry:
    subject: str
    phase: str
    choice: str
    alternatives: str
    rationale: str
    counter: str
    superseded: tuple[DecisionEntry, ...] = ()


@dataclass(frozen=True)
class DecisionLog:
    groups: tuple[tuple[str, tuple[DecisionEntry, ...]], ...]


@dataclass(frozen=True)
class PhaseDetail:
    subject: str
    effort: str
    title: str
    state: str
    awaiting_signoff: bool
    body: str
    decisions: list[RelatedRecord]
    constraints: list[RelatedRecord]
    tasks: list[TaskRow]
    evidence: PhaseEvidence | None = None
    spec_body: str = ""
    design_body: str = ""
    structured: bool = False
    milestone: str = ""
    milestone_title: str = ""
    proof: ProofView | None = None


def tabs_for(detail: PhaseDetail) -> tuple[str, ...]:
    """Full tab set for a structured phase; simple set otherwise (R1)."""
    base = TABS if detail.structured else SIMPLE_TABS
    if detail.proof is None:
        return tuple(name for name in base if name != "proof")
    return base


def _decision_entry(
    record: Record,
    by_id: dict[str, Record],
    history: bool,
) -> DecisionEntry:
    facts = decision_facts(record)
    body = record.get("body") or ""
    superseded: tuple[DecisionEntry, ...] = ()
    if history:
        kids: list[DecisionEntry] = []
        for ref in (record.get("relationships") or {}).get("supersedes") or []:
            predecessor = by_id.get(ref)
            if predecessor is not None:
                kids.append(_decision_entry(predecessor, by_id, history))
        superseded = tuple(kids)
    return DecisionEntry(
        subject=record["subject"],
        phase=facts.phase,
        choice=facts.choice,
        alternatives=facts.alternatives,
        rationale=body_section_ci(body, "Rationale"),
        counter=body_section_ci(body, "Counter-argument"),
        superseded=superseded,
    )


def load_decision_log(
    target: Project,
    effort: str,
    phase: str | None,
    history: bool,
) -> DecisionLog:
    """Phase- or effort-scoped decisions, with optional superseded chains (R7)."""
    effort_phases = sorted(
        (
            phase
            for phase in current_phase_models(list_records(target, PHASE_TYPE))
            if phase.effort == effort
        ),
        key=lambda phase: (phase.ordinal, phase.subject),
    )
    titles = {phase.subject: phase.title or phase.subject for phase in effort_phases}

    listed = list_records(target, DECISION_TYPE, payload={"effort": effort})
    by_id = {record["id"]: record for record in listed}
    if history:
        for record in list_records(
            target,
            DECISION_TYPE,
            state="superseded",
            payload={"effort": effort},
        ):
            by_id.setdefault(record["id"], record)

    active = [
        record
        for record in by_id.values()
        if record.get("lifecycle_state") not in INACTIVE_STATES
        and _in_effort(record, effort)
        and (phase is None or record_scope(record).phase == phase)
    ]
    active.sort(key=lambda record: (record["subject"], record["id"]))

    grouped: dict[str, list[DecisionEntry]] = {}
    for record in active:
        phase_subject = decision_facts(record).phase
        title = titles.get(phase_subject, phase_subject)
        grouped.setdefault(title, []).append(_decision_entry(record, by_id, history))

    ordered_titles = [
        titles[phase.subject] for phase in effort_phases if titles[phase.subject] in grouped
    ]
    for title in grouped:
        if title not in ordered_titles:
            ordered_titles.append(title)
    return DecisionLog(tuple((title, tuple(grouped[title])) for title in ordered_titles))


def load_phase_detail(target: Project, effort: str, phase_subject: str) -> PhaseDetail:
    """Load one phase with its body, decisions, constraints, and tasks."""

    def by_effort(record_type: str) -> dict[str | None, list[Record]]:
        return records_by_effort(list_records(target, record_type))

    snapshot_phases = by_effort(PHASE_TYPE).get(effort, [])
    phase = current_phase_model(phase_subject, snapshot_phases)
    if phase is None:
        raise ModelError(f"phase {phase_subject} not found in {effort}")
    record = phase.record
    tasks = records_by_effort(list_records(target, WORK_ITEM_TYPE)).get(effort, [])
    effort_acceptances = by_effort(ACCEPTANCE_TYPE).get(effort, [])
    effort_checks = by_effort(CHECK_RUN_TYPE).get(effort, [])
    decision_records = by_effort(DECISION_TYPE).get(effort, [])
    row = next(
        (
            p
            for p in phase_rows(
                [record],
                tasks,
                effort_acceptances,
                effort_checks,
                small_wave_budget_minutes=configured_small_wave_budget(target, tasks),
            )
        ),
        None,
    )
    phase_specs = list_records(target, SPECIFICATION, payload={"phase": phase_subject})
    phase_designs = list_records(target, DESIGN_TYPE, payload={"phase": phase_subject})
    spec = newest_record(records_for_phase(phase_specs, phase_subject, effort))
    design = newest_record(records_for_phase(phase_designs, phase_subject, effort))
    evidence = phase_evidence(
        phase_subject,
        effort,
        phase_specs,
        phase_designs,
        decision_records,
        tasks,
        effort_acceptances,
        effort_checks,
        by_effort(ASSESSMENT_TYPE).get(effort, []),
        by_effort(INTEGRATION_REPORT_TYPE).get(effort, []),
        by_effort(RELEASE_TYPE).get(effort, []),
        snapshot_phases,
        load_phase_progress(target, current_token(target)).get(phase_subject),
    )
    decisions = [
        RelatedRecord("decision", r["id"], r["subject"], decision_facts(r).choice)
        for r in decision_records
        if decision_facts(r).phase == phase_subject and r["lifecycle_state"] not in INACTIVE_STATES
    ]
    constraints = [
        RelatedRecord("constraint", r["id"], r["subject"], constraint_facts(r).statement)
        for r in by_effort(CONSTRAINT_TYPE).get(effort, [])
        if constraint_facts(r).applies_to == phase_subject
        and r["lifecycle_state"] not in INACTIVE_STATES
    ]
    milestone_slug = phase.milestone or ""
    milestone_title = ""
    if milestone_slug:
        milestone_record = next(
            (
                r
                for r in by_effort(MILESTONE_TYPE).get(effort, [])
                if r["subject"] == milestone_slug and r["lifecycle_state"] in LIVE_PHASE_STATES
            ),
            None,
        )
        if milestone_record is not None:
            milestone_title = milestone_facts(milestone_record).title
        else:
            milestone_title = milestone_slug
    packet = proof_packet(list_records(target, PROOF_PACKET), phase)
    proof = None
    if packet is not None:
        proof_body = packet.record.get("body") or ""
        proof = ProofView(
            id=packet.id,
            kind=packet.kind,
            revision=packet.revision,
            base=packet.base or "",
            look=body_section_ci(proof_body, "Look"),
            attention=body_section_ci(proof_body, "Attention"),
            machine=body_section_ci(proof_body, "Machine"),
            diff=body_section_ci(proof_body, "Diff"),
        )
    return PhaseDetail(
        subject=phase_subject,
        effort=effort,
        title=phase.title,
        state=record["lifecycle_state"],
        awaiting_signoff=bool(row and row.awaiting_signoff),
        body=phase.body,
        decisions=decisions,
        constraints=constraints,
        tasks=[
            t
            for t in task_rows(
                tasks,
                list_records(target, ASSIGNMENT),
                phases=[record],
                small_wave_budget_minutes=configured_small_wave_budget(target, tasks),
            )
            if t.phase == phase_subject
        ],
        evidence=evidence,
        spec_body=(spec.get("body") or "") if spec else "",
        design_body=(design.get("body") or "") if design else "",
        structured=spec is not None,
        milestone=milestone_slug,
        milestone_title=milestone_title,
        proof=proof,
    )


def _assessed(record: Record, phase: str, requirement: str) -> bool:
    facts = assessment_facts(record)
    return facts.phase == phase and facts.requirement == requirement


def _in_effort(record: Record, effort: str) -> bool:
    return record_scope(record).effort in (None, "", effort)


def load_requirement_detail(
    target: Project, effort: str, phase: str, requirement: str
) -> RequirementDetail:
    """Load one requirement, including superseded assessments oldest first."""

    def listed(record_type: str, state: str | None = None) -> list[Record]:
        return list_records(target, record_type, state=state)

    specs = listed(SPECIFICATION)
    by_id = {record["id"]: record for record in listed(ASSESSMENT_TYPE)}
    for record in listed(ASSESSMENT_TYPE, "superseded"):
        by_id.setdefault(record["id"], record)
    history = [
        record
        for record in by_id.values()
        if _assessed(record, phase, requirement) and _in_effort(record, effort)
    ]
    history = _oldest_first(history)
    active = [record for record in history if record.get("lifecycle_state") not in INACTIVE_STATES]
    latest = newest_record(active)
    spec = light_specification(phase, effort, listed(PHASE_TYPE)) or newest_record(
        records_for_phase(specs, phase, effort)
    )
    text = _texts_for(listed(PHASE_TYPE), spec, phase).get(requirement, "")
    traced = [
        task
        for task in tasks_by_requirement(listed(WORK_ITEM_TYPE), phase).get(requirement, [])
        if _in_effort(task, effort)
    ]
    traced.sort(key=lambda record: record["subject"])
    subjects: list[str] = []
    for task in traced:
        for subject in work_item_facts(task).decisions:
            if subject not in subjects:
                subjects.append(subject)
    acceptances = [
        record
        for record in records_for_phase(listed(ACCEPTANCE_TYPE), phase, effort)
        if requirement in acceptance_requirement_ids(record)
    ]
    acceptances.sort(key=recorded_at)
    check_records = listed(CHECK_RUN_TYPE)
    check_map = latest_checks(check_records)
    pool = _live_pool(
        [spec] if spec is not None else [],
        records_for_phase(listed(ACCEPTANCE_TYPE), phase, effort),
        check_records,
        active,
    )
    status, nxt, _ = _assessment_view(latest, requirement_status(pool, phase).get(requirement))
    assignments = listed(ASSIGNMENT)
    return RequirementDetail(
        phase,
        requirement,
        text,
        status,
        nxt,
        _choices(subjects, listed(DECISION_TYPE)),
        tuple(
            row
            for row in task_rows(
                traced,
                assignments,
                small_wave_budget_minutes=configured_small_wave_budget(target, traced),
            )
            if row.phase == phase
        ),
        tuple(
            AcceptanceRow(
                acceptance.id,
                acceptance.subject,
                acceptance.criteria or "",
                acceptance.method,
                acceptance.verify_command,
                check_map.get(acceptance.id),
            )
            for acceptance in map(read_acceptance, acceptances)
        ),
        tuple(
            AssessmentView(
                record["id"],
                facts.status,
                facts.level,
                facts.next,
                facts.confidence,
            )
            for record, facts in ((record, assessment_facts(record)) for record in history)
        ),
    )
