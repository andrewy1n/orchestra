from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor import suite
from orchestra.conductor.gate import format_missing, gate_terms_for, missing_terms
from orchestra.conductor.head_evidence import (
    EvidenceIndex,
    acceptance_latest,
    latest,
    latest_review,
    review_at_head,
    suite_check_runs,
)
from orchestra.conductor.landing import (
    LandingProofState,
    landing_proof_state,
    parse_landing,
    phase_place,
    proof_packet,
)
from orchestra.score.analyze import analyze_phase
from orchestra.score.lookups import closing_work_item, current_phase, live_work_items
from orchestra.score.lookups import dependencies as item_dependencies
from orchestra.score.phase import Phase
from orchestra.score.workflow_blockers import phase_blockers
from orchestra.score.workflow_reviews import Step, step_readiness
from orchestra.tools import Absent, BranchState, Git, Merged, ReadFailed, Unmerged, branch_state

Stage = Literal["spec", "design", "tasks", "execute", "verify", "land", "close"]
StageStatus = Literal["done", "current", "pending", "blocked", "unknown"]
VerifyStep = Literal["analyze", "suite", "reviewer", "integration-report", "gate", "proof"]
IntegrationState = Literal["not-required", "missing", "failing", "passing"]

STAGES: tuple[Stage, ...] = ("spec", "design", "tasks", "execute", "verify", "land", "close")


class PhaseProgressError(ValueError):
    pass


@dataclass(frozen=True)
class StageState:
    stage: Stage
    status: StageStatus


@dataclass(frozen=True)
class Readiness:
    ready: bool
    reason: str = ""


@dataclass(frozen=True)
class ExecutionVerdict:
    result: str
    verdict: str


@dataclass(frozen=True)
class TaskFact:
    subject: str
    lifecycle_state: str
    report: ExecutionVerdict | None


@dataclass(frozen=True)
class AcceptanceHold:
    subject: str
    has_run: bool
    holds: bool


@dataclass(frozen=True)
class VerifyFacts:
    suite_reason: str
    review_at_head: bool
    gate_missing: tuple[str, ...]
    proof_at_head: bool


@dataclass(frozen=True)
class HumanGateFact:
    subject: str


@dataclass(frozen=True)
class PrerequisiteFact:
    subject: str
    lifecycle_state: str


@dataclass(frozen=True)
class PhaseFacts:
    phase: Phase
    lifecycle: str
    spec: Readiness
    design: Readiness
    tasks_review: Readiness
    plan: Readiness
    tasks: tuple[TaskFact, ...]
    acceptances: tuple[AcceptanceHold, ...]
    integration: IntegrationState
    verify: VerifyFacts | None
    landing: LandingProofState | None
    branch: BranchState | None
    gates: tuple[HumanGateFact, ...]
    prerequisites: tuple[PrerequisiteFact, ...]

    @property
    def weight(self) -> Literal["light", "full"] | None:
        return self.phase.weight


@dataclass(frozen=True)
class PhaseProgress:
    stages: tuple[StageState, ...]
    current: Stage | None
    reason: str
    blocked_by: tuple[str, ...]


def execution_readiness(tasks: Sequence[TaskFact]) -> Readiness:
    if not tasks:
        return Readiness(False, "execution requires a nonempty task plan")
    for task in tasks:
        if task.lifecycle_state != "done":
            return Readiness(False, f"task {task.subject!r} is not done")
        report = task.report
        if report is None:
            return Readiness(False, f"task {task.subject!r} has no execution report")
        if report.result != "pass" or report.verdict != "pass":
            return Readiness(
                False,
                f"task {task.subject!r} execution report "
                f"result={report.result!r}, verdict={report.verdict!r}",
            )
    return Readiness(True)


def verification_readiness(
    acceptances: Sequence[AcceptanceHold], integration: IntegrationState
) -> Readiness:
    if not acceptances:
        return Readiness(False, "phase has no active acceptances")
    for acceptance in acceptances:
        if not acceptance.has_run:
            return Readiness(False, f"acceptance {acceptance.subject!r} has no check-run")
        if not acceptance.holds:
            return Readiness(False, f"acceptance {acceptance.subject!r} check-run is not pass")
    if integration == "missing":
        return Readiness(False, "phase integration report is missing")
    if integration == "failing":
        return Readiness(False, "phase integration report is not passing")
    return Readiness(True)


def open_verify_step(
    acceptances: Sequence[AcceptanceHold], integration: IntegrationState, verify: VerifyFacts
) -> VerifyStep | None:
    if not acceptances or not all(acceptance.holds for acceptance in acceptances):
        return "analyze"
    if verify.suite_reason:
        return "suite"
    if not verify.review_at_head:
        return "reviewer"
    if integration in ("missing", "failing"):
        return "integration-report"
    if verify.gate_missing:
        return "gate"
    if not verify.proof_at_head:
        return "proof"
    return None


def _land_reason(landing: LandingProofState | None) -> str:
    match landing:
        case None | "no-landing":
            return "no-landing"
        case "no-packet":
            return "no-packet"
        case "not-at-head":
            return "stale-proof"
        case "failed":
            return "failed-landing"
        case "landed":
            return "landed"


def _close_state(branch: BranchState | None) -> tuple[str, StageStatus]:
    match branch:
        case None:
            return "branch-unread", "unknown"
        case Unmerged():
            return "awaiting-merge", "current"
        case Merged() | Absent():
            return "ready-to-close", "current"
        case ReadFailed():
            return "git-read-failed", "unknown"


def _assess_done() -> PhaseProgress:
    return PhaseProgress(tuple(StageState(stage, "done") for stage in STAGES), None, "", ())


def _blockers(facts: PhaseFacts) -> tuple[tuple[str, ...], str]:
    gates = tuple(gate.subject for gate in facts.gates)
    prerequisites = tuple(
        item.subject for item in facts.prerequisites if item.lifecycle_state != "done"
    )
    parts: list[str] = []
    if gates:
        parts.append("human gate: " + ", ".join(gates))
    if prerequisites:
        parts.append("prerequisite phase not done: " + ", ".join(prerequisites))
    return gates + prerequisites, "; ".join(parts)


def _first_open(facts: PhaseFacts) -> tuple[Stage, str, StageStatus]:
    if not facts.spec.ready:
        return "spec", facts.spec.reason or "spec review is missing", "current"
    if not facts.design.ready:
        return "design", facts.design.reason or "design review is missing", "current"
    if not facts.tasks_review.ready:
        return "tasks", facts.tasks_review.reason or "tasks review is missing", "current"
    if not facts.plan.ready:
        return "tasks", facts.plan.reason or "task plan is not ready", "current"
    execution = execution_readiness(facts.tasks)
    if not execution.ready:
        return "execute", execution.reason, "current"
    if facts.verify is None:
        return "verify", "verify facts unavailable", "unknown"
    step = open_verify_step(facts.acceptances, facts.integration, facts.verify)
    if step is not None:
        return "verify", step, "current"
    if facts.landing != "landed":
        return "land", _land_reason(facts.landing), "current"
    reason, status = _close_state(facts.branch)
    return "close", reason, status


def assess(facts: PhaseFacts) -> PhaseProgress:
    if facts.lifecycle == "done":
        return _assess_done()
    current, reason, status = _first_open(facts)
    blocked_by, blocked_reason = _blockers(facts)
    if blocked_by:
        status = "blocked"
        reason = blocked_reason
    position = STAGES.index(current)
    stages = tuple(
        StageState(
            stage, "done" if index < position else status if index == position else "pending"
        )
        for index, stage in enumerate(STAGES)
    )
    return PhaseProgress(stages, current, reason, blocked_by)


def _text(record: Record, field: str) -> str:
    value = record["payload"].get(field)
    return value if isinstance(value, str) else ""


def _active_acceptances(records: Sequence[Record], phase: str) -> list[Record]:
    return [
        record
        for record in records
        if record["record_type"] == "score:acceptance"
        and record["payload"].get("phase") == phase
        and record["lifecycle_state"] == "active"
    ]


def plan_readiness(records: Sequence[Record], phase: str) -> Readiness:
    report = analyze_phase(list(records), phase, stage="plan")
    errors = [finding.message for finding in report.findings if finding.severity == "error"]
    if errors:
        return Readiness(False, "; ".join(errors))
    if not live_work_items(phase, records) or not _active_acceptances(records, phase):
        return Readiness(False, "analyzed task plan requires work-items and active acceptances")
    return Readiness(True)


def review_readiness(records: Sequence[Record], phase: Phase, step: Step) -> Readiness:
    readiness = step_readiness(list(records), phase.subject, step)
    if readiness.status != "ready":
        return Readiness(False, readiness.reason or f"{step} review is {readiness.status}")
    if (
        step == "tasks"
        and readiness.review is not None
        and readiness.review["payload"].get("authority") == "task-plan-policy"
    ):
        effort = next(
            (
                record
                for record in records
                if record["record_type"] == "score:effort"
                and record["subject"] == phase.effort
                and record["lifecycle_state"] != "superseded"
            ),
            None,
        )
        if effort is None:
            return Readiness(False, f"required effort {phase.effort!r} could not be read")
        if effort["payload"].get("autonomy") not in ("auto-plan", "auto-phases"):
            return Readiness(False, "task-plan policy does not permit this review")
    return Readiness(True)


def task_facts(records: Sequence[Record], phase: str) -> tuple[TaskFact, ...]:
    reports = [
        record for record in records if record["record_type"] == "conductor:execution-report"
    ]
    facts: list[TaskFact] = []
    for item in live_work_items(phase, records):
        own = [
            report for report in reports if report["payload"].get("work_item") == item["subject"]
        ]
        report = max(own, key=lambda row: (row["recorded_at"], row["id"])) if own else None
        verdict = (
            ExecutionVerdict(_text(report, "result"), _text(report, "verdict"))
            if report is not None
            else None
        )
        facts.append(TaskFact(item["subject"], item["lifecycle_state"], verdict))
    return tuple(facts)


def acceptance_holds(records: Sequence[Record], phase: str) -> tuple[AcceptanceHold, ...]:
    index = EvidenceIndex(list(records))
    holds: list[AcceptanceHold] = []
    for acceptance in _active_acceptances(records, phase):
        answer = acceptance_latest(index, acceptance, None)
        holds.append(AcceptanceHold(acceptance["subject"], answer.run is not None, answer.holds))
    return tuple(holds)


def requires_integration_report(records: Sequence[Record], phase: str) -> bool:
    items = {item["subject"]: item for item in live_work_items(phase, records)}
    closing = closing_work_item(phase, records)
    dependencies = {
        subject: set(item_dependencies(item)) & items.keys() for subject, item in items.items()
    }
    implementation_tasks = set(items) - ({closing["subject"]} if closing is not None else set())
    completed: set[str] = set()
    while implementation_tasks - completed:
        wave = {
            subject
            for subject in implementation_tasks - completed
            if dependencies[subject] <= completed
        }
        if len(wave) != 1:
            return True
        completed.update(wave)
    return False


def integration_state(records: Sequence[Record], phase: Phase) -> IntegrationState:
    if not requires_integration_report(records, phase.subject):
        return "not-required"
    reports = [
        record
        for record in records
        if record["record_type"] == "conductor:integration-report"
        and record["payload"].get("phase") == phase.subject
        and record["payload"].get("effort") == phase.effort
    ]
    if not reports:
        return "missing"
    newest = max(reports, key=lambda row: (row["recorded_at"], row["id"]))
    if newest["payload"].get("result") != "pass" or not _text(newest, "revision"):
        return "failing"
    return "passing"


def verify_facts(
    project: Project,
    records: Sequence[Record],
    phase: Phase,
    git: Callable[[Path], Git] = Git,
) -> VerifyFacts:
    index = EvidenceIndex(list(records))
    review = latest_review(index, phase.subject, phase.effort)
    head = _text(review, "revision") if review is not None else ""
    check_runs = [record for record in records if record["record_type"] == "tuner:check-run"]
    policy = suite.load_suite_policy(project.project_root)
    latest_suite = latest(suite_check_runs(index, phase.subject))
    suite_head = head or (_text(latest_suite, "revision") if latest_suite is not None else "")
    suite_reason = suite.suite_ready_for_review(
        policy, check_runs, phase_slug=phase.subject, phase_head=suite_head
    )
    at_head = review_at_head(index, phase.subject, phase.effort, head).holds
    place = phase_place(phase, project.project_root)
    missing = missing_terms(gate_terms_for(list(records), phase, place, policy, git_at=git))
    return VerifyFacts(
        suite_reason=suite_reason,
        review_at_head=at_head,
        gate_missing=tuple(format_missing(missing)),
        proof_at_head=proof_packet(records, phase, head) is not None,
    )


def verify_step(
    project: Project,
    records: Sequence[Record],
    phase: Phase,
    git: Callable[[Path], Git] = Git,
) -> VerifyStep | None:
    return open_verify_step(
        acceptance_holds(records, phase.subject),
        integration_state(records, phase),
        verify_facts(project, records, phase, git),
    )


def _gates(records: Sequence[Record], phase: Phase) -> tuple[HumanGateFact, ...]:
    return tuple(
        HumanGateFact(blocker.record["subject"])
        for blocker in phase_blockers(list(records), phase.subject)
    )


def _prerequisites(records: Sequence[Record], phase: Phase) -> tuple[PrerequisiteFact, ...]:
    raw = phase.record["payload"].get("depends_on", [])
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise PhaseProgressError(f"phase {phase.subject!r} has invalid dependencies")
    facts: list[PrerequisiteFact] = []
    for subject in (item for item in raw if isinstance(item, str)):
        record = current_phase(subject, records)
        if record is None:
            raise PhaseProgressError(f"required phase {subject!r} could not be read")
        facts.append(PrerequisiteFact(subject, record["lifecycle_state"]))
    return tuple(facts)


def _landed_branch(project: Project, phase: Phase) -> BranchState:
    place = phase_place(phase, project.project_root)
    return branch_state(place.repo, place.branch, place.base)


def phase_facts(
    project: Project,
    records: Sequence[Record],
    phase: Phase,
    *,
    git: Callable[[Path], Git] = Git,
) -> PhaseFacts:
    lifecycle = phase.record["lifecycle_state"]
    spec = review_readiness(records, phase, "spec")
    design = review_readiness(records, phase, "design")
    tasks_review = review_readiness(records, phase, "tasks")
    plan = plan_readiness(records, phase.subject)
    tasks = task_facts(records, phase.subject)
    reached_verify = (
        spec.ready
        and design.ready
        and tasks_review.ready
        and plan.ready
        and execution_readiness(tasks).ready
        and lifecycle != "done"
    )
    has_landing = parse_landing(phase.body).present
    landing = landing_proof_state(records, phase) if has_landing else None
    return PhaseFacts(
        phase=phase,
        lifecycle=lifecycle,
        spec=spec,
        design=design,
        tasks_review=tasks_review,
        plan=plan,
        tasks=tasks,
        acceptances=acceptance_holds(records, phase.subject),
        integration=integration_state(records, phase),
        verify=verify_facts(project, records, phase, git) if reached_verify else None,
        landing=landing,
        branch=_landed_branch(project, phase) if reached_verify and landing == "landed" else None,
        gates=_gates(records, phase),
        prerequisites=_prerequisites(records, phase),
    )
