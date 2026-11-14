from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

from orchestra.canon.errors import StaleWriteError
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor.gate import format_missing, gate_terms, missing_terms, parse_landing
from orchestra.conductor.head_evidence import EvidenceIndex, acceptance_latest
from orchestra.conductor.landing import latest_landing
from orchestra.score.analyze import analyze_phase
from orchestra.score.workflow_blockers import WorkflowBlockerError, phase_blockers
from orchestra.score.workflow_reviews import Step, step_readiness
from orchestra.score.workflow_selection import PhaseSelectionError, resolve_phase_selection

Operation = Literal["phase", "prepare", "deliver", "single-step"]
ActionState = Literal["ready", "blocked"]

_VERSION = "1"
_PHASE_STEPS: tuple[Step, ...] = ("spec", "design", "tasks", "execute", "verify", "land")
_STEPS_BY_OPERATION: dict[Operation, tuple[Step, ...]] = {
    "phase": _PHASE_STEPS,
    "prepare": ("spec", "design"),
    "deliver": ("tasks", "execute", "verify", "land"),
    "single-step": (),
}
_LEGACY_STEPS: dict[Operation, tuple[Step, ...]] = {
    "phase": ("spec", "design", "tasks", "execute", "verify"),
    "deliver": ("tasks", "execute", "verify"),
}


class WorkflowRunError(ValueError):
    pass


@dataclass(frozen=True)
class RunPreview:
    effort: str
    operation: Operation
    phases: tuple[str, ...]
    external_dependencies: tuple[str, ...]
    requested_steps: tuple[Step, ...]
    change_token: str


@dataclass(frozen=True)
class RunAction:
    phase: str
    step: Step
    state: ActionState
    reason: str = ""


@dataclass(frozen=True)
class RunStatus:
    run: Record
    complete: bool
    incomplete: bool
    actions: tuple[RunAction, ...]


def _operation(value: str) -> Operation:
    match value:
        case "phase" | "prepare" | "deliver" | "single-step":
            return value
        case _:
            raise WorkflowRunError(f"unsupported playbook {value!r}")


def _step(value: str | None) -> Step | None:
    match value:
        case "spec" | "design" | "tasks" | "execute" | "verify" | "land":
            return value
        case _:
            return None


def _requested_steps(operation: Operation, step: str | None) -> tuple[Step, ...]:
    if operation == "single-step":
        selected = _step(step)
        if selected is None:
            raise WorkflowRunError("single-step operation requires one supported workflow step")
        return (selected,)
    if step is not None:
        raise WorkflowRunError("step is only valid for the single-step operation")
    return _STEPS_BY_OPERATION[operation]


def preview_run(
    project: Project,
    effort: str,
    selector: str,
    operation: str,
    *,
    step: str | None = None,
) -> RunPreview:
    selected_operation = _operation(operation)
    requested_steps = _requested_steps(selected_operation, step)
    token = project.change_token()
    records = project.records()
    if project.change_token() != token:
        raise StaleWriteError("store changed while the run preview was being read")
    try:
        selection = resolve_phase_selection(records, effort, selector)
    except PhaseSelectionError as exc:
        raise WorkflowRunError(str(exc)) from exc
    return RunPreview(
        effort,
        selected_operation,
        selection.dependency_order,
        tuple(sorted(selection.external_dependencies)),
        requested_steps,
        token,
    )


def start_run(project: Project, preview: RunPreview) -> Record:
    operation = _operation(preview.operation)
    steps = _requested_steps(
        operation,
        preview.requested_steps[0]
        if operation == "single-step" and preview.requested_steps
        else None,
    )
    if steps != preview.requested_steps or not preview.phases:
        raise WorkflowRunError("run preview is invalid")
    records = project.records()
    for subject in preview.phases:
        phase = _current_phase(records, subject)
        if _text(phase, "effort") != preview.effort:
            raise WorkflowRunError(f"phase {subject!r} belongs to another effort")
    subject = f"{preview.effort}-{preview.operation}-{uuid4().hex[:12]}"
    project.apply_at_snapshot(
        [
            {
                "op": "create",
                "type": "score:run",
                "subject": subject,
                "payload": {
                    "effort": preview.effort,
                    "operation": preview.operation,
                    "phases": list(preview.phases),
                    "requested_steps": list(preview.requested_steps),
                    "definition_version": _VERSION,
                },
            }
        ],
        preview.change_token,
    )
    return project.resolve("score:run", subject)


def _text(record: Record, field: str) -> str:
    value = record["payload"].get(field)
    return value if isinstance(value, str) else ""


def _run_steps(run: Record) -> tuple[Step, ...]:
    payload = run["payload"]
    operation = _operation(_text(run, "operation"))
    raw = payload.get("requested_steps")
    if not isinstance(raw, list):
        raise WorkflowRunError(f"run {run['subject']!r} has invalid requested steps")
    steps_list: list[Step] = []
    for item in raw:
        step = _step(item if isinstance(item, str) else None)
        if step is None:
            raise WorkflowRunError(f"run {run['subject']!r} has invalid requested steps")
        steps_list.append(step)
    steps = tuple(steps_list)
    expected = _requested_steps(
        operation, steps[0] if operation == "single-step" and steps else None
    )
    if steps != expected and steps != _LEGACY_STEPS.get(operation):
        raise WorkflowRunError(f"run {run['subject']!r} has invalid operation steps")
    return steps


def _phase_records(records: list[Record], run: Record) -> list[Record]:
    phases = run["payload"].get("phases")
    if not isinstance(phases, list) or not all(isinstance(item, str) for item in phases):
        raise WorkflowRunError(f"run {run['subject']!r} has invalid phase selection")
    selected: list[Record] = []
    for subject in phases:
        phase = next(
            (
                record
                for record in records
                if record["record_type"] == "score:phase"
                and record["subject"] == subject
                and record["lifecycle_state"] != "superseded"
            ),
            None,
        )
        if phase is None:
            raise WorkflowRunError(f"run {run['subject']!r} requires missing phase {subject!r}")
        if _text(phase, "effort") != _text(run, "effort"):
            raise WorkflowRunError(
                f"run {run['subject']!r} phase {subject!r} has a different effort"
            )
        selected.append(phase)
    return selected


def _dependencies(phase: Record) -> list[str]:
    raw = phase["payload"].get("depends_on", [])
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise WorkflowRunError(f"phase {phase['subject']!r} has invalid dependencies")
    return [item for item in raw if isinstance(item, str)]


def _current_phase(records: list[Record], subject: str) -> Record:
    phase = next(
        (
            record
            for record in records
            if record["record_type"] == "score:phase"
            and record["subject"] == subject
            and record["lifecycle_state"] != "superseded"
        ),
        None,
    )
    if phase is None:
        raise WorkflowRunError(f"required phase {subject!r} could not be read")
    return phase


def _plan_ready(records: list[Record], phase: str) -> tuple[bool, str]:
    report = analyze_phase(records, phase, stage="plan")
    errors = [finding.message for finding in report.findings if finding.severity == "error"]
    if errors:
        return False, "; ".join(errors)
    items = [
        record
        for record in records
        if record["record_type"] == "score:work-item"
        and record["payload"].get("phase") == phase
        and record["lifecycle_state"] in ("planned", "in_progress", "done")
    ]
    acceptances = [
        record
        for record in records
        if record["record_type"] == "score:acceptance"
        and record["payload"].get("phase") == phase
        and record["lifecycle_state"] == "active"
    ]
    if not items or not acceptances:
        return False, "analyzed task plan requires work-items and active acceptances"
    return True, ""


def _review_ready(records: list[Record], phase: str, step: Step) -> tuple[bool, str]:
    readiness = step_readiness(records, phase, step)
    if readiness.status == "ready":
        if (
            step == "tasks"
            and readiness.review is not None
            and readiness.review["payload"].get("authority") == "task-plan-policy"
        ):
            phase_record = _current_phase(records, phase)
            effort_subject = _text(phase_record, "effort")
            effort = next(
                (
                    record
                    for record in records
                    if record["record_type"] == "score:effort"
                    and record["subject"] == effort_subject
                    and record["lifecycle_state"] != "superseded"
                ),
                None,
            )
            if effort is None:
                return False, f"required effort {effort_subject!r} could not be read"
            if effort["payload"].get("autonomy") not in ("auto-plan", "auto-phases"):
                return False, "task-plan policy does not permit this review"
        return True, ""
    return False, readiness.reason or f"{step} review is {readiness.status}"


def _execution_ready(records: list[Record], phase: str) -> tuple[bool, str]:
    items = [
        record
        for record in records
        if record["record_type"] == "score:work-item"
        and record["payload"].get("phase") == phase
        and record["lifecycle_state"] in ("planned", "in_progress", "done")
    ]
    if not items:
        return False, "execution requires a nonempty task plan"
    reports = [
        record for record in records if record["record_type"] == "conductor:execution-report"
    ]
    for item in items:
        if item["lifecycle_state"] != "done":
            return False, f"task {item['subject']!r} is not done"
        own = [
            report for report in reports if report["payload"].get("work_item") == item["subject"]
        ]
        if not own:
            return False, f"task {item['subject']!r} has no execution report"
        report = max(own, key=lambda row: (row["recorded_at"], row["id"]))
        if report["payload"].get("result") != "pass" or report["payload"].get("verdict") != "pass":
            result = report["payload"].get("result")
            verdict = report["payload"].get("verdict")
            return False, (
                f"task {item['subject']!r} execution report result={result!r}, verdict={verdict!r}"
            )
    return True, ""


def _requires_integration_report(records: list[Record], phase: str) -> bool:
    items = {
        record["subject"]: record
        for record in records
        if record["record_type"] == "score:work-item"
        and record["payload"].get("phase") == phase
        and record["lifecycle_state"] in ("planned", "in_progress", "done")
    }
    dependencies: dict[str, set[str]] = {}
    for subject, item in items.items():
        raw = item["payload"].get("depends_on", [])
        if not isinstance(raw, list) or not all(isinstance(dep, str) for dep in raw):
            return True
        dependencies[subject] = {dep for dep in raw if isinstance(dep, str)} & items.keys()
    closing_tasks = {
        subject
        for subject, task_dependencies in dependencies.items()
        if len(items) > 1 and len(task_dependencies) == len(items) - 1
    }
    implementation_tasks = set(items) - closing_tasks
    completed: set[str] = set()
    while implementation_tasks - completed:
        wave = {
            subject
            for subject in implementation_tasks - completed
            if dependencies[subject] <= completed
        }
        if not wave:
            return True
        if len(wave) > 1:
            return True
        completed.update(wave)
    return False


def _verification_ready(records: list[Record], phase: str) -> tuple[bool, str]:
    phase_record = _current_phase(records, phase)
    acceptances = [
        record
        for record in records
        if record["record_type"] == "score:acceptance"
        and record["payload"].get("phase") == phase
        and record["lifecycle_state"] == "active"
    ]
    if not acceptances:
        return False, "phase has no active acceptances"
    index = EvidenceIndex(records)
    for acceptance in acceptances:
        answer = acceptance_latest(index, acceptance, None)
        if answer.run is None:
            return False, f"acceptance {acceptance['subject']!r} has no check-run"
        if not answer.holds:
            return False, f"acceptance {acceptance['subject']!r} check-run is not pass"
    if _requires_integration_report(records, phase):
        effort = _text(phase_record, "effort")
        integrations = [
            record
            for record in records
            if record["record_type"] == "conductor:integration-report"
            and record["payload"].get("phase") == phase
            and record["payload"].get("effort") == effort
        ]
        if not integrations:
            return False, "phase integration report is missing"
        latest = max(integrations, key=lambda row: (row["recorded_at"], row["id"]))
        if latest["payload"].get("result") != "pass" or not _text(latest, "revision"):
            return False, "phase integration report is not passing"
    return True, ""


def _verification_gate(project: Project, records: list[Record], phase: str) -> tuple[bool, str]:
    ready, reason = _verification_ready(records, phase)
    if not ready:
        return False, reason
    phase_record = _current_phase(records, phase)
    if phase_record["lifecycle_state"] == "done":
        return True, ""
    if not parse_landing(phase_record.get("body") or "").present:
        return False, "phase is not closed"
    try:
        missing = missing_terms(
            gate_terms(project.project_root, phase, store_dir=project.store_path)
        )
    except LookupError as exc:
        raise WorkflowRunError(str(exc)) from exc
    if missing:
        return False, "phase gate is not met: " + "; ".join(format_missing(missing))
    if _proof_packet(records, phase) is None:
        return False, "phase has no proof packet"
    return True, ""


def _proof_packet(records: list[Record], phase: str) -> Record | None:
    packets = [
        record
        for record in records
        if record["record_type"] == "conductor:proof-packet" and record["subject"] == phase
    ]
    return max(packets, key=lambda row: (row["recorded_at"], row["id"])) if packets else None


def _landing_ready(records: list[Record], phase: str) -> tuple[bool, str]:
    phase_record = _current_phase(records, phase)
    if phase_record["lifecycle_state"] == "done":
        return True, ""
    if not parse_landing(phase_record.get("body") or "").present:
        return True, ""
    landing = latest_landing(records, phase)
    if landing is None:
        return False, "phase has no landing record"
    if landing["payload"].get("result") != "success":
        return False, "latest landing did not succeed"
    latest = _proof_packet(records, phase)
    if latest is None:
        return False, "phase has no proof packet"
    if landing["payload"].get("head_sha") != latest["payload"].get("revision"):
        return False, "landing is not at the proof packet head"
    return True, ""


def _step_completion(
    project: Project, records: list[Record], phase: str, step: Step
) -> tuple[bool, str]:
    if step in ("spec", "design", "tasks"):
        ready, reason = _review_ready(records, phase, step)
        if not ready:
            return False, reason
        if step == "tasks":
            return _plan_ready(records, phase)
        return True, ""
    if step == "execute":
        return _execution_ready(records, phase)
    if step == "land":
        return _landing_ready(records, phase)
    return _verification_gate(project, records, phase)


def _action_for(
    project: Project,
    records: list[Record],
    phase: Record,
    step: Step,
    *,
    prepare: bool = False,
    selected_phases: set[str] | None = None,
) -> RunAction:
    subject = phase["subject"]
    try:
        blockers = phase_blockers(records, subject)
    except WorkflowBlockerError as exc:
        return RunAction(subject, step, "blocked", str(exc))
    if blockers:
        names = ", ".join(blocker.record["subject"] for blocker in blockers)
        return RunAction(subject, step, "blocked", f"human decision blocks this phase: {names}")
    for dependency in _dependencies(phase):
        if prepare and selected_phases is not None and dependency in selected_phases:
            continue
        dependency_record = _current_phase(records, dependency)
        if dependency_record["lifecycle_state"] != "done":
            return RunAction(
                subject, step, "blocked", f"prerequisite phase {dependency!r} is not done"
            )
    prerequisites: dict[Step, Step | None] = {
        "spec": None,
        "design": "spec",
        "tasks": "design",
        "execute": "tasks",
        "verify": "execute",
        "land": "verify",
    }
    prerequisite = prerequisites[step]
    if prerequisite is not None:
        complete, reason = _step_completion(project, records, subject, prerequisite)
        if not complete:
            return RunAction(
                subject, step, "blocked", f"{prerequisite} prerequisite is incomplete: {reason}"
            )
    if step == "spec":
        readiness = step_readiness(records, subject, step)
        if readiness.status == "blocked":
            return RunAction(
                subject, step, "blocked", readiness.reason or "specification is blocked"
            )
        return RunAction(subject, step, "ready")
    if step == "design":
        return RunAction(subject, step, "ready")
    if step == "tasks":
        return RunAction(subject, step, "ready")
    if step == "execute":
        ready, reason = _execution_ready(records, subject)
        if not ready and "execution report result=" in reason:
            return RunAction(subject, step, "blocked", reason)
        return RunAction(subject, step, "ready", reason if not ready else "")
    return RunAction(subject, step, "ready")


def _all_actions(project: Project, records: list[Record], run: Record) -> tuple[RunAction, ...]:
    steps = _run_steps(run)
    phases = _phase_records(records, run)
    actions: list[RunAction] = []
    prepare_barrier = _text(run, "operation") == "prepare"
    selected_phases = {phase["subject"] for phase in phases}
    specs_complete = all(
        _step_completion(project, records, phase["subject"], "spec")[0] for phase in phases
    )
    for phase in phases:
        for step in steps:
            complete, _ = _step_completion(project, records, phase["subject"], step)
            if complete:
                continue
            if prepare_barrier and step == "design" and not specs_complete:
                break
            actions.append(
                _action_for(
                    project,
                    records,
                    phase,
                    step,
                    prepare=prepare_barrier,
                    selected_phases=selected_phases,
                )
            )
            break
    return tuple(actions)


def _find_run(records: list[Record], subject: str) -> Record:
    run = next(
        (
            record
            for record in records
            if record["record_type"] == "score:run"
            and (record["subject"] == subject or record["id"] == subject)
            and record["lifecycle_state"] != "superseded"
        ),
        None,
    )
    if run is None:
        raise WorkflowRunError(f"required workflow run {subject!r} could not be read")
    return run


def next_actions(project: Project, run_subject: str) -> tuple[RunAction, ...]:
    records = project.records()
    run = _find_run(records, run_subject)
    return _all_actions(project, records, run)


def run_status(project: Project, run_subject: str) -> RunStatus:
    records = project.records()
    run = _find_run(records, run_subject)
    actions = _all_actions(project, records, run)
    complete = not actions
    return RunStatus(run, complete, not complete, actions)
