from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal
from uuid import uuid4

from orchestra.canon.errors import RecordShapeError, StaleWriteError
from orchestra.canon.project import Project
from orchestra.canon.project_config import load_project_config
from orchestra.canon.types import Record
from orchestra.conductor import phase_progress
from orchestra.conductor.gate import format_missing, gate_terms, missing_terms
from orchestra.conductor.landing import (
    LandingProofError,
    LandingProofState,
    ProofPacket,
    landing_proof_state,
    parse_landing,
    proof_packet,
)
from orchestra.score.phase import Phase, current_phase_model
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
    brief: str = ""


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
        if phase.effort != preview.effort:
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


def _phase_records(records: list[Record], run: Record) -> list[Phase]:
    phases = run["payload"].get("phases")
    if not isinstance(phases, list) or not all(isinstance(item, str) for item in phases):
        raise WorkflowRunError(f"run {run['subject']!r} has invalid phase selection")
    selected: list[Phase] = []
    for subject in (item for item in phases if isinstance(item, str)):
        phase = _read_current_phase(records, subject)
        if phase is None:
            raise WorkflowRunError(f"run {run['subject']!r} requires missing phase {subject!r}")
        if phase.effort != _text(run, "effort"):
            raise WorkflowRunError(
                f"run {run['subject']!r} phase {subject!r} has a different effort"
            )
        selected.append(phase)
    return selected


def _dependencies(phase: Phase) -> list[str]:
    raw = phase.record["payload"].get("depends_on", [])
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise WorkflowRunError(f"phase {phase.subject!r} has invalid dependencies")
    return [item for item in raw if isinstance(item, str)]


def _read_current_phase(records: list[Record], subject: str) -> Phase | None:
    try:
        return current_phase_model(subject, records)
    except RecordShapeError as exc:
        raise WorkflowRunError(str(exc)) from exc


def _current_phase(records: list[Record], subject: str) -> Phase:
    phase = _read_current_phase(records, subject)
    if phase is None:
        raise WorkflowRunError(f"required phase {subject!r} could not be read")
    return phase


def _plan_ready(records: list[Record], phase: str) -> tuple[bool, str]:
    readiness = phase_progress.plan_readiness(records, phase)
    return readiness.ready, readiness.reason


def _review_ready(records: list[Record], phase: str, step: Step) -> tuple[bool, str]:
    readiness = phase_progress.review_readiness(records, _current_phase(records, phase), step)
    return readiness.ready, readiness.reason


def _execution_ready(records: list[Record], phase: str) -> tuple[bool, str]:
    readiness = phase_progress.execution_readiness(phase_progress.task_facts(records, phase))
    return readiness.ready, readiness.reason


def _verification_ready(records: list[Record], phase: str) -> tuple[bool, str]:
    current = _current_phase(records, phase)
    readiness = phase_progress.verification_readiness(
        phase_progress.acceptance_holds(records, phase),
        phase_progress.integration_state(records, current),
    )
    return readiness.ready, readiness.reason


def _verification_gate(project: Project, records: list[Record], phase: str) -> tuple[bool, str]:
    ready, reason = _verification_ready(records, phase)
    if not ready:
        return False, reason
    current = _current_phase(records, phase)
    if current.record["lifecycle_state"] == "done":
        return True, ""
    if not parse_landing(current.body).present:
        return False, "phase is not closed"
    try:
        missing = missing_terms(
            gate_terms(project.project_root, phase, store_dir=project.store_path)
        )
    except (LookupError, RecordShapeError) as exc:
        raise WorkflowRunError(str(exc)) from exc
    if missing:
        return False, "phase gate is not met: " + "; ".join(format_missing(missing))
    if _proof_packet(records, current) is None:
        return False, "phase has no proof packet"
    return True, ""


_LANDING_REASONS: dict[LandingProofState, str] = {
    "landed": "",
    "no-landing": "phase has no landing record",
    "failed": "latest landing did not succeed",
    "no-packet": "phase has no proof packet",
    "not-at-head": "landing is not at the proof packet head",
}


def _proof_packet(
    records: list[Record], phase: Phase, head: str | None = None
) -> ProofPacket | None:
    try:
        return proof_packet(records, phase, head)
    except RecordShapeError as exc:
        raise WorkflowRunError(str(exc)) from exc


def _landing_proof_state(records: list[Record], phase: Phase) -> LandingProofState:
    try:
        return landing_proof_state(records, phase)
    except (LandingProofError, RecordShapeError) as exc:
        raise WorkflowRunError(str(exc)) from exc


def _landing_ready(records: list[Record], phase: str) -> tuple[bool, str]:
    current = _current_phase(records, phase)
    if current.record["lifecycle_state"] == "done":
        return True, ""
    if not parse_landing(current.body).present:
        return True, ""
    state = _landing_proof_state(records, current)
    return state == "landed", _LANDING_REASONS[state]


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
    phase: Phase,
    step: Step,
    *,
    prepare: bool = False,
    selected_phases: set[str] | None = None,
) -> RunAction:
    subject = phase.subject
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
        if dependency_record.record["lifecycle_state"] != "done":
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


def _verify_stage(project: Project, records: list[Record], phase: str) -> str | None:
    try:
        step = phase_progress.verify_step(project, records, _current_phase(records, phase))
    except RecordShapeError as exc:
        raise WorkflowRunError(str(exc)) from exc
    return "reviewer" if step == "integration-report" else step


def _land_stage(project: Project, records: list[Record], phase: str) -> str | None:
    current = _current_phase(records, phase)
    if current.record["lifecycle_state"] == "done":
        return None
    if not parse_landing(current.body).present:
        return None
    match _landing_proof_state(records, current):
        case "landed":
            return "close"
        case "failed":
            config = load_project_config(project.project_root)
            return "repair-ci" if config.land_adapter == "github-pr" else "land"
        case "no-landing" | "no-packet" | "not-at-head":
            return "land"


def step_stage(project: Project, records: list[Record], phase: str, step: str) -> str | None:
    match step:
        case "verify":
            return _verify_stage(project, records, phase)
        case "land":
            return _land_stage(project, records, phase)
        case _:
            return None


def _with_brief(project: Project, action: RunAction) -> RunAction:
    if action.state != "ready":
        return action
    from orchestra.conductor.briefs.context import brief_context
    from orchestra.conductor.briefs.render import render_brief

    text = render_brief(brief_context(project, action.phase, action.step))
    return replace(action, brief=text)


def phase_step_action(project: Project, phase: str, step: Step) -> RunAction:
    records = project.records()
    return _with_brief(project, _action_for(project, records, _current_phase(records, phase), step))


def _all_actions(
    project: Project, records: list[Record], run: Record, *, with_brief: bool
) -> tuple[RunAction, ...]:
    steps = _run_steps(run)
    phases = _phase_records(records, run)
    actions: list[RunAction] = []
    prepare_barrier = _text(run, "operation") == "prepare"
    selected_phases = {phase.subject for phase in phases}
    specs_complete = all(
        _step_completion(project, records, phase.subject, "spec")[0] for phase in phases
    )
    for phase in phases:
        for step in steps:
            complete, _ = _step_completion(project, records, phase.subject, step)
            if complete:
                continue
            if prepare_barrier and step == "design" and not specs_complete:
                break
            action = _action_for(
                project,
                records,
                phase,
                step,
                prepare=prepare_barrier,
                selected_phases=selected_phases,
            )
            actions.append(_with_brief(project, action) if with_brief else action)
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
    return _all_actions(project, records, run, with_brief=True)


def run_status(project: Project, run_subject: str) -> RunStatus:
    records = project.records()
    run = _find_run(records, run_subject)
    actions = _all_actions(project, records, run, with_brief=False)
    complete = not actions
    return RunStatus(run, complete, not complete, actions)
