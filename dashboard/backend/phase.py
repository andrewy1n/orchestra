"""Phase rows, phase evidence, phase detail, decision log, and requirement detail."""

from __future__ import annotations

from orchestra.canon import record_payload
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from orchestra.canon.project import Project
from dashboard.backend import store
from dashboard.backend.records import (
    INACTIVE_STATES,
    _by_effort,
    _derived,
    _items,
    _list,
    _live,
    _merge_aliases,
    _newest,
    _recorded_at,
    _remapped,
    _section,
)
from dashboard.backend.store import ModelError
from dashboard.backend.task import (
    AcceptanceRow,
    CheckRun,
    RelatedRecord,
    TaskRow,
    _belongs,
    _check_from,
    _latest_checks,
    _task_rows,
)


LIVE_PHASE_STATES = ("planned", "in_progress", "done")
COUNTED_TASK_STATES = ("planned", "in_progress", "done")
LOOP_NEXT = ("specify", "design", "plan", "execute", "integrate", "verify", "release")


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
    evidence: "PhaseEvidence | None" = None
    sitting: str = ""
    body: str = ""
    elapsed_minutes: int | None = None
    unset_estimates: int = 0
    suite: str = ""
    milestone: str = ""
    milestone_title: str = ""


@dataclass(frozen=True)
class MilestoneRow:
    subject: str
    title: str
    ordinal: int
    state: str
    done: int
    total: int
    id: str = ""


def _requirement_texts(body: str) -> dict[str, str]:
    texts = {}
    for line in _section(body, "Requirements").splitlines():
        ident, sep, text = line.partition(":")
        if sep and ident.strip():
            texts[ident.strip()] = text.strip()
    return texts


def _oldest_first(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for start in sorted(
        (record for record in records if record["id"] not in pointed), key=_recorded_at
    ):
        chain: list[dict[str, Any]] = []
        current: dict[str, Any] | None = start
        while current is not None and current["id"] not in seen:
            seen.add(current["id"])
            chain.append(current)
            current = by_id.get(previous.get(current["id"], ""))
        chain.reverse()
        ordered.extend(chain)
    ordered.extend(
        sorted((record for record in records if record["id"] not in seen), key=_recorded_at)
    )
    return ordered


def _for_phase(records: list[dict[str, Any]], phase: str, effort: str) -> list[dict[str, Any]]:
    matched = []
    for record in _live(records):
        payload = record_payload(record)
        record_effort = payload.get("effort")
        if record_effort and record_effort != effort:
            continue
        if payload.get("phase") == phase:
            matched.append(record)
    return matched


def _latest_assessment_map(records: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for record in sorted(_live(records), key=_recorded_at):
        payload = record_payload(record)
        grouped[(payload.get("phase", ""), payload.get("requirement", ""))] = record
    return grouped


def _traced_records(
    tasks: list[dict[str, Any]], phase: str, requirement: str
) -> list[dict[str, Any]]:
    return [
        task
        for task in tasks
        if task.get("lifecycle_state") != "superseded"
        and record_payload(task).get("phase") == phase
        and requirement in _items(record_payload(task).get("requirements"))
    ]


def _choices(subjects: list[str], decisions: list[dict[str, Any]]) -> tuple["DecisionChoice", ...]:
    by_subject: dict[str, dict[str, Any]] = {}
    for record in sorted(_live(decisions), key=_recorded_at):
        by_subject[record["subject"]] = record
    return tuple(
        DecisionChoice(
            subject,
            record_payload(by_subject[subject]).get("choice", "") if subject in by_subject else "",
        )
        for subject in subjects
    )


def _latest_requirement_check(
    requirement: str,
    phase: str,
    acceptances: list[dict[str, Any]],
    checks: list[dict[str, Any]],
) -> "CheckRun | None":
    acceptance_ids = {
        record["id"]
        for record in acceptances
        if record.get("lifecycle_state") not in INACTIVE_STATES
        and record_payload(record).get("phase") == phase
    }
    matched = [
        record
        for record in checks
        if record.get("lifecycle_state") not in INACTIVE_STATES
        and record_payload(record).get("requirement") == requirement
        and record_payload(record).get("criterion_id") in acceptance_ids
    ]
    record = _newest(matched)
    return _check_from(record) if record else None


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


# Suite check-run convention (shared with suite-engine):
# subject `<phase>-suite`, evidence_kind `integration`, revision = phase head SHA.
# Legacy `<phase>-tier2` is read for display only when no suite check-run exists.
# In-flight: result `blocked` and body contains a running marker (no final pass/fail yet).
SUITE_SUBJECT_SUFFIX = "-suite"
LEGACY_TIER2_SUBJECT_SUFFIX = "-tier2"
SUITE_EVIDENCE_KIND = "integration"
SUITE_RUNNING_MARKER = "suite-running"
LEGACY_TIER2_RUNNING_MARKER = "tier2-running"


def _short_revision(revision: str) -> str:
    rev = (revision or "").strip()
    if not rev:
        return "?"
    return rev[:7]


def _suite_check_for_phase(phase: str, checks: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Newest active suite check-run for phase; fall back to legacy `-tier2`."""

    def matching(suffix: str) -> list[dict[str, Any]]:
        return [
            record
            for record in checks
            if record.get("lifecycle_state") not in INACTIVE_STATES
            and record.get("subject") == f"{phase}{suffix}"
            and (record_payload(record).get("evidence_kind") or "") == SUITE_EVIDENCE_KIND
        ]

    record = _newest(matching(SUITE_SUBJECT_SUFFIX))
    if record is not None:
        return record
    return _newest(matching(LEGACY_TIER2_SUBJECT_SUFFIX))


def suite_status_label(phase: str, checks: list[dict[str, Any]]) -> str:
    """Compact suite chrome for a phase header: suite running / suite ok@SHA / suite fail@SHA."""
    record = _suite_check_for_phase(phase, checks)
    if record is None:
        return ""
    payload = record_payload(record)
    result = payload.get("result") or ""
    body = record.get("body") or ""
    if result == "blocked" and (
        SUITE_RUNNING_MARKER in body or LEGACY_TIER2_RUNNING_MARKER in body
    ):
        return "suite running"
    short = _short_revision(payload.get("revision") or "")
    if result == "pass":
        return f"suite ok@{short}"
    if result == "fail":
        return f"suite fail@{short}"
    return ""


def phase_elapsed(tasks: list[TaskRow]) -> tuple[int | None, int]:
    """Wave-rule minutes for already-counted tasks, plus how many lack an estimate.

    An inline wave sums its estimates. Any other wave contributes its longest.
    A task with no wave is its own group. Blank estimates are skipped, and zero counts.
    """
    unset = sum(task.estimate_minutes is None for task in tasks)
    groups: dict[Any, list[TaskRow]] = {}
    for task in tasks:
        key = task.wave if task.wave is not None else task.id
        groups.setdefault(key, []).append(task)

    def order(key: Any) -> tuple:
        return (0, key) if isinstance(key, int) else (1, str(key))

    figures: list[int] = []
    for key in sorted(groups, key=order):
        members = groups[key]
        values = [task.estimate_minutes for task in members if task.estimate_minutes is not None]
        if not values:
            continue
        if all(task.executor == "inline" for task in members):
            figures.append(sum(values))
        else:
            figures.append(max(values))
    if not figures:
        return (None, unset)
    return (sum(figures), unset)


def _awaits_signoff(
    task: dict[str, Any],
    others: list[str],
    acceptances: list[dict[str, Any]],
    latest: dict[str, "CheckRun"],
) -> bool:
    effort = record_payload(task).get("effort", "")
    mine = [
        record
        for record in acceptances
        if record["lifecycle_state"] not in INACTIVE_STATES
        and _belongs(record, task["subject"], effort, others)
    ]
    runs = [latest.get(record["id"]) for record in mine]
    if not mine or any(run is None or run.result != "pass" for run in runs):
        return False
    return any(run is not None and run.method == "manual" and not run.signed_by for run in runs)


def _phase_rows(
    records: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    acceptances: list[dict[str, Any]] | None = None,
    checks: list[dict[str, Any]] | None = None,
    evidence_by_phase: dict[str, "PhaseEvidence"] | None = None,
) -> list[PhaseRow]:
    latest = _latest_checks(checks or [])
    evidence_by_phase = evidence_by_phase or {}
    subjects = [task["subject"] for task in tasks]
    counted = [task for task in tasks if task["lifecycle_state"] in COUNTED_TASK_STATES]
    rows = []
    for record in records:
        if record["lifecycle_state"] not in LIVE_PHASE_STATES:
            continue
        members = [
            task for task in counted if record_payload(task).get("phase") == record["subject"]
        ]
        payload = record_payload(record)
        open_tasks = [task for task in members if task["lifecycle_state"] != "done"]
        awaiting = (
            record["lifecycle_state"] != "done"
            and bool(open_tasks)
            and all(
                _awaits_signoff(
                    task, [s for s in subjects if s != task["subject"]], acceptances or [], latest
                )
                for task in open_tasks
            )
        )
        elapsed_minutes, unset_estimates = phase_elapsed(_task_rows(members))
        body = record.get("body") or ""
        rows.append(
            PhaseRow(
                subject=record["subject"],
                title=payload.get("title", ""),
                ordinal=payload.get("ordinal", 0),
                state=record["lifecycle_state"],
                done=sum(t["lifecycle_state"] == "done" for t in members),
                total=len(members),
                id=record["id"],
                awaiting_signoff=awaiting,
                evidence=evidence_by_phase.get(record["subject"]),
                sitting=sitting_phrase(body),
                body=body,
                elapsed_minutes=elapsed_minutes,
                unset_estimates=unset_estimates,
                suite=suite_status_label(record["subject"], checks or []),
                milestone=payload.get("milestone") or "",
            )
        )
    rows.sort(key=lambda row: (row.ordinal, row.subject))
    return rows


def _milestone_state(members: list[PhaseRow]) -> str:
    if any(phase.state == "in_progress" for phase in members):
        return "in_progress"
    if members and all(phase.state == "done" for phase in members):
        return "done"
    return "planned"


def _milestone_rows(records: list[dict[str, Any]], phases: list[PhaseRow]) -> list[MilestoneRow]:
    by_slug: dict[str, list[PhaseRow]] = {}
    for phase in phases:
        if phase.milestone:
            by_slug.setdefault(phase.milestone, []).append(phase)
    rows: list[MilestoneRow] = []
    for record in records:
        if record["lifecycle_state"] not in LIVE_PHASE_STATES:
            continue
        payload = record_payload(record)
        members = by_slug.get(record["subject"], [])
        rows.append(
            MilestoneRow(
                subject=record["subject"],
                title=payload.get("title") or record["subject"],
                ordinal=payload.get("ordinal", 0),
                state=_milestone_state(members),
                done=sum(phase.state == "done" for phase in members),
                total=len(members),
                id=record["id"],
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

    def sort_key(phase: PhaseRow) -> tuple:
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
    latest_check: "CheckRun | None"
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
    tasks: tuple["TaskRow", ...]
    acceptances: tuple["AcceptanceRow", ...]
    assessments: tuple[AssessmentView, ...]


def _stage(
    phase: str,
    effort: str,
    spec_ids: list[str],
    designs: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    acceptances: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    assessments: list[dict[str, Any]],
    reports: list[dict[str, Any]],
    releases: list[dict[str, Any]],
) -> tuple[str, bool]:
    latest_release = _newest(_for_phase(releases, phase, effort))
    if latest_release and record_payload(latest_release).get("state") == "ready":
        return "release", True
    latest = {
        requirement: record
        for (record_phase, requirement), record in _latest_assessment_map(assessments).items()
        if record_phase == phase
    }
    non_verified = [
        record for record in latest.values() if record_payload(record).get("status") != "verified"
    ]
    if non_verified:

        def rank(record: dict[str, Any]) -> int:
            nxt = record_payload(record).get("next", "")
            return LOOP_NEXT.index(nxt) if nxt in LOOP_NEXT else len(LOOP_NEXT)

        return record_payload(min(non_verified, key=rank)).get("next", ""), False
    if spec_ids and all(
        record_payload(latest.get(req) or {}).get("status") == "verified" for req in spec_ids
    ):
        return "release", False
    if not _for_phase(designs, phase, effort):
        return "design", False
    counted = [
        task
        for task in tasks
        if record_payload(task).get("phase") == phase
        and task.get("lifecycle_state") in COUNTED_TASK_STATES
    ]
    if not counted:
        return "plan", False
    if any(task.get("lifecycle_state") != "done" for task in counted):
        return "execute", False
    waves: dict[Any, int] = {}
    for task in counted:
        wave = _derived(task).get("wave")
        waves[wave] = waves.get(wave, 0) + 1
    passing = any(
        record_payload(report).get("result") == "pass"
        for report in _for_phase(reports, phase, effort)
    )
    if any(count > 1 for count in waves.values()) and not passing:
        return "integrate", False
    checked = {
        record_payload(check).get("criterion_id")
        for check in checks
        if check.get("lifecycle_state") not in INACTIVE_STATES
    }
    if any(
        record_payload(record).get("requirement") and record["id"] not in checked
        for record in _for_phase(acceptances, phase, effort)
    ):
        return "verify", False
    return "assess", False


def _phase_evidence(
    phase: str,
    effort: str,
    specs: list[dict[str, Any]],
    designs: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    acceptances: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    assessments: list[dict[str, Any]],
    reports: list[dict[str, Any]],
    releases: list[dict[str, Any]],
) -> PhaseEvidence | None:
    spec = _newest(_for_phase(specs, phase, effort))
    if spec is None:
        return None
    spec_ids = _items(record_payload(spec).get("requirements"))
    texts = _requirement_texts(spec.get("body") or "")
    latest = {
        requirement: record
        for (record_phase, requirement), record in _latest_assessment_map(assessments).items()
        if record_phase == phase
    }
    rows = []
    for requirement in spec_ids:
        assessment = latest.get(requirement)
        if assessment is None:
            status, nxt, confidence = "unassessed", "", ""
        else:
            payload = record_payload(assessment)
            status = payload.get("status", "")
            nxt = "" if status == "verified" else payload.get("next", "")
            confidence = payload.get("confidence", "")
        traced = _traced_records(tasks, phase, requirement)
        check = _latest_requirement_check(requirement, phase, acceptances, checks)
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
    design = _newest(_for_phase(designs, phase, effort))
    subjects = _items(record_payload(design).get("decisions")) if design else []
    report = _newest(_for_phase(reports, phase, effort))
    integration = None
    if report is not None:
        integration = IntegrationView(
            record_payload(report).get("result", ""),
            _section(report.get("body") or "", "Conflicts"),
        )
    stage, release_ready = _stage(
        phase,
        effort,
        spec_ids,
        designs,
        tasks,
        acceptances,
        checks,
        assessments,
        reports,
        releases,
    )
    latest_release = _newest(_for_phase(releases, phase, effort))
    release_state = record_payload(latest_release).get("state", "") if latest_release else ""
    return PhaseEvidence(
        phase,
        record_payload(spec).get("weight", ""),
        tuple(rows),
        stage,
        integration,
        release_ready,
        _choices(subjects, decisions),
        _section(spec.get("body") or "", "Non-goals"),
        release_state=release_state,
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
    superseded: tuple["DecisionEntry", ...] = ()


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
    record: dict[str, Any],
    by_id: dict[str, dict[str, Any]],
    history: bool,
) -> DecisionEntry:
    payload = record_payload(record)
    body = record.get("body") or ""
    superseded: tuple[DecisionEntry, ...] = ()
    if history:
        kids = []
        for ref in (record.get("relationships") or {}).get("supersedes") or []:
            predecessor = by_id.get(ref)
            if predecessor is not None:
                kids.append(_decision_entry(predecessor, by_id, history))
        superseded = tuple(kids)
    return DecisionEntry(
        subject=record["subject"],
        phase=payload.get("phase", ""),
        choice=payload.get("choice", ""),
        alternatives=payload.get("alternatives", "") or "",
        rationale=_section(body, "Rationale"),
        counter=_section(body, "Counter-argument"),
        superseded=superseded,
    )


def load_decision_log(
    target: Project,
    effort: str,
    phase: str | None,
    history: bool,
) -> DecisionLog:
    """Phase- or effort-scoped decisions, with optional superseded chains (R7)."""
    aliases = _merge_aliases(_list(target, "score:effort"))
    phase_records = [
        record
        for record in _remapped(_list(target, "score:phase"), aliases)
        if record_payload(record).get("effort") == effort
    ]
    phase_records.sort(
        key=lambda record: (record_payload(record).get("ordinal", 0), record["subject"])
    )
    titles = {
        record["subject"]: record_payload(record).get("title") or record["subject"]
        for record in phase_records
    }

    listed = _remapped(
        _list(target, "score:decision", payload={"effort": effort}),
        aliases,
    )
    by_id = {record["id"]: record for record in listed}
    if history:
        for record in _remapped(
            _list(
                target,
                "score:decision",
                state="superseded",
                payload={"effort": effort},
            ),
            aliases,
        ):
            by_id.setdefault(record["id"], record)

    active = [
        record
        for record in by_id.values()
        if record.get("lifecycle_state") not in INACTIVE_STATES
        and record_payload(record).get("effort") in (None, "", effort)
        and (phase is None or record_payload(record).get("phase") == phase)
    ]
    active.sort(key=lambda record: (record["subject"], record["id"]))

    grouped: dict[str, list[DecisionEntry]] = {}
    for record in active:
        phase_subject = record_payload(record).get("phase") or ""
        title = titles.get(phase_subject, phase_subject)
        grouped.setdefault(title, []).append(_decision_entry(record, by_id, history))

    ordered_titles = [
        titles[record["subject"]]
        for record in phase_records
        if titles[record["subject"]] in grouped
    ]
    for title in grouped:
        if title not in ordered_titles:
            ordered_titles.append(title)
    return DecisionLog(tuple((title, tuple(grouped[title])) for title in ordered_titles))


def load_phase_detail(target: Project, effort: str, phase_subject: str) -> PhaseDetail:
    """Load one phase with its body, decisions, constraints, and tasks."""
    aliases = _merge_aliases(_list(target, "score:effort"))

    def by_effort(record_type: str) -> dict[str, list[dict[str, Any]]]:
        return _by_effort(_remapped(_list(target, record_type), aliases))

    snapshot_phases = by_effort("score:phase").get(effort, [])
    record = next((r for r in snapshot_phases if r["subject"] == phase_subject), None)
    if record is None:
        raise ModelError(f"phase {phase_subject} not found in {effort}")
    item = store.get_record(target, record["id"], "score:phase")
    tasks = _by_effort(_list(target, "score:work-item")).get(effort, [])
    effort_acceptances = by_effort("score:acceptance").get(effort, [])
    effort_checks = by_effort("tuner:check-run").get(effort, [])
    decision_records = by_effort("score:decision").get(effort, [])
    row = next(
        (p for p in _phase_rows([record], tasks, effort_acceptances, effort_checks)),
        None,
    )
    phase_specs = _remapped(
        _list(target, "score:specification", payload={"phase": phase_subject}),
        aliases,
    )
    phase_designs = _remapped(
        _list(target, "score:design", payload={"phase": phase_subject}),
        aliases,
    )
    spec = _newest(_for_phase(phase_specs, phase_subject, effort))
    design = _newest(_for_phase(phase_designs, phase_subject, effort))
    evidence = _phase_evidence(
        phase_subject,
        effort,
        phase_specs,
        phase_designs,
        decision_records,
        tasks,
        effort_acceptances,
        effort_checks,
        by_effort("conductor:assessment").get(effort, []),
        by_effort("conductor:integration-report").get(effort, []),
        by_effort("conductor:release").get(effort, []),
    )
    decisions = [
        RelatedRecord("decision", r["id"], r["subject"], record_payload(r).get("choice", ""))
        for r in decision_records
        if record_payload(r).get("phase") == phase_subject
        and r["lifecycle_state"] not in INACTIVE_STATES
    ]
    constraints = [
        RelatedRecord("constraint", r["id"], r["subject"], record_payload(r).get("statement", ""))
        for r in by_effort("score:constraint").get(effort, [])
        if record_payload(r).get("applies_to") == phase_subject
        and r["lifecycle_state"] not in INACTIVE_STATES
    ]
    payload = record_payload(record)
    milestone_slug = payload.get("milestone") or ""
    milestone_title = ""
    if milestone_slug:
        milestone_record = next(
            (
                r
                for r in by_effort("score:milestone").get(effort, [])
                if r["subject"] == milestone_slug and r["lifecycle_state"] in LIVE_PHASE_STATES
            ),
            None,
        )
        if milestone_record is not None:
            milestone_title = record_payload(milestone_record).get("title") or milestone_slug
        else:
            milestone_title = milestone_slug
    proof_records = [
        r
        for r in _remapped(
            _list(
                target,
                "conductor:proof-packet",
                payload={"phase": phase_subject},
            ),
            aliases,
        )
        if record_payload(r).get("effort") in (None, "", effort)
    ]
    proof_record = _newest(proof_records)
    proof = None
    if proof_record is not None:
        proof_body = proof_record.get("body") or ""
        proof_payload = record_payload(proof_record)
        proof = ProofView(
            id=proof_record["id"],
            kind=proof_payload.get("kind") or "",
            revision=proof_payload.get("revision") or "",
            base=proof_payload.get("base") or "",
            look=_section(proof_body, "Look"),
            attention=_section(proof_body, "Attention"),
            machine=_section(proof_body, "Machine"),
            diff=_section(proof_body, "Diff"),
        )
    return PhaseDetail(
        subject=phase_subject,
        effort=effort,
        title=payload.get("title", ""),
        state=record["lifecycle_state"],
        awaiting_signoff=bool(row and row.awaiting_signoff),
        body=item.get("body") or "",
        decisions=decisions,
        constraints=constraints,
        tasks=[t for t in _task_rows(tasks, phases=[record]) if t.phase == phase_subject],
        evidence=evidence,
        spec_body=(spec.get("body") or "") if spec else "",
        design_body=(design.get("body") or "") if design else "",
        structured=spec is not None,
        milestone=milestone_slug,
        milestone_title=milestone_title,
        proof=proof,
    )


def load_requirement_detail(
    target: Project, effort: str, phase: str, requirement: str
) -> RequirementDetail:
    """Load one requirement, including superseded assessments oldest first."""
    aliases = _merge_aliases(_list(target, "score:effort"))

    def listed(record_type: str, state: str | None = None) -> list[dict[str, Any]]:
        return _remapped(_list(target, record_type, state=state), aliases)

    specs = listed("score:specification")
    by_id = {record["id"]: record for record in listed("conductor:assessment")}
    for record in listed("conductor:assessment", "superseded"):
        by_id.setdefault(record["id"], record)
    history = [
        record
        for record in by_id.values()
        if record_payload(record).get("phase") == phase
        and record_payload(record).get("requirement") == requirement
        and record_payload(record).get("effort") in (None, "", effort)
    ]
    history = _oldest_first(history)
    active = [record for record in history if record.get("lifecycle_state") not in INACTIVE_STATES]
    latest = _newest(active)
    if latest is None:
        status, nxt = "unassessed", ""
    else:
        status, nxt = (
            record_payload(latest).get("status", ""),
            record_payload(latest).get("next", ""),
        )
    spec = _newest(_for_phase(specs, phase, effort))
    text = _requirement_texts(spec.get("body") or "").get(requirement, "") if spec else ""
    traced = [
        task
        for task in _traced_records(listed("score:work-item"), phase, requirement)
        if record_payload(task).get("effort") in (None, "", effort)
    ]
    traced.sort(key=lambda record: record["subject"])
    subjects: list[str] = []
    for task in traced:
        for subject in _items(record_payload(task).get("decisions")):
            if subject not in subjects:
                subjects.append(subject)
    acceptances = [
        record
        for record in _for_phase(listed("score:acceptance"), phase, effort)
        if record_payload(record).get("requirement") == requirement
    ]
    acceptances.sort(key=_recorded_at)
    latest_checks = _latest_checks(listed("tuner:check-run"))
    return RequirementDetail(
        phase,
        requirement,
        text,
        status,
        nxt,
        _choices(subjects, listed("score:decision")),
        tuple(row for row in _task_rows(traced) if row.phase == phase),
        tuple(
            AcceptanceRow(
                record["id"],
                record["subject"],
                record_payload(record).get("criterion", ""),
                record_payload(record).get("method", ""),
                record_payload(record).get("verify_command", ""),
                latest_checks.get(record["id"]),
            )
            for record in acceptances
        ),
        tuple(
            AssessmentView(
                record["id"],
                record_payload(record).get("status", ""),
                record_payload(record).get("level") or "",
                record_payload(record).get("next", ""),
                record_payload(record).get("confidence", ""),
            )
            for record in history
        ),
    )
