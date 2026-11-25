from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Literal
from uuid import uuid4

from orchestra.canon.errors import RecordShapeError, StaleWriteError
from orchestra.canon.project import Project
from orchestra.canon.project_config import load_project_config
from orchestra.canon.types import Record
from orchestra.conductor.landing.landing import LandingProofError
from orchestra.conductor.phases.progress import phase_progress
from orchestra.conductor.phases.progress.phase_progress import (
    PhaseProgress,
    PhaseProgressError,
    assess,
)
from orchestra.score.lookups import live_work_items
from orchestra.score.planning.phase import Phase, current_phase_model
from orchestra.score.planning.standing_constraint import applicable, declared_areas
from orchestra.score.workflow.workflow_blockers import (
    WorkflowBlockerError,
    blocked_tasks,
    phase_blockers,
)
from orchestra.score.workflow.workflow_reviews import Step, step_readiness
from orchestra.score.workflow.workflow_selection import PhaseSelectionError, resolve_phase_selection

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


_PREREQUISITES: dict[Step, Step | None] = {
    "spec": None,
    "design": "spec",
    "tasks": "design",
    "execute": "tasks",
    "verify": "execute",
    "land": "verify",
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


def start_previewed_run(project: Project, preview: RunPreview, snapshot_token: str) -> Record:
    if preview.change_token != snapshot_token:
        raise StaleWriteError("snapshot changed; preview again before starting")
    return start_run(project, preview)


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


def _progress(project: Project, records: list[Record], phase: Phase) -> PhaseProgress:
    try:
        facts = phase_progress.phase_facts(project, records, phase)
    except (
        LandingProofError,
        LookupError,
        PhaseProgressError,
        RecordShapeError,
        WorkflowBlockerError,
    ) as exc:
        raise WorkflowRunError(str(exc)) from exc
    return assess(replace(facts, gates=(), prerequisites=()))


def _stage_done(progress: PhaseProgress, step: Step) -> bool:
    return any(state.stage == step and state.status == "done" for state in progress.stages)


def _action_for(
    project: Project,
    records: list[Record],
    phase: Phase,
    step: Step,
    progress: PhaseProgress,
    *,
    prepare: bool = False,
    selected_phases: set[str] | None = None,
) -> RunAction:
    subject = phase.subject
    try:
        blockers = phase_blockers(records, subject)
    except WorkflowBlockerError as exc:
        return RunAction(subject, step, "blocked", str(exc))
    if blockers and step == "execute" and all(blocker.scope == "task" for blocker in blockers):
        items = live_work_items(subject, records)
        held = blocked_tasks(items, blockers)
        derived = project.derived(records)
        if any(
            item["subject"] not in held
            and item["lifecycle_state"] in ("planned", "in_progress")
            and derived.get(item["id"], {}).get("ready")
            for item in items
        ):
            blockers = []
    if blockers:
        names = ", ".join(blocker.task or blocker.record["subject"] for blocker in blockers)
        return RunAction(subject, step, "blocked", f"human decision blocks this phase: {names}")
    for dependency in _dependencies(phase):
        if prepare and selected_phases is not None and dependency in selected_phases:
            continue
        dependency_record = _current_phase(records, dependency)
        if dependency_record.record["lifecycle_state"] != "done":
            return RunAction(
                subject, step, "blocked", f"prerequisite phase {dependency!r} is not done"
            )
    prerequisite = _PREREQUISITES[step]
    if prerequisite is not None and not _stage_done(progress, prerequisite):
        return RunAction(
            subject,
            step,
            "blocked",
            f"{progress.current or prerequisite} prerequisite is incomplete: {progress.reason}",
        )
    if step == "spec":
        readiness = step_readiness(records, subject, step)
        if readiness.status == "blocked":
            return RunAction(
                subject, step, "blocked", readiness.reason or "specification is blocked"
            )
        return RunAction(subject, step, "ready")
    if step == "execute" and progress.current == "execute":
        if "execution report result=" in progress.reason:
            return RunAction(subject, step, "blocked", progress.reason)
        return RunAction(subject, step, "ready", progress.reason)
    return RunAction(subject, step, "ready")


def _verify_stage(project: Project, records: list[Record], phase: str) -> str | None:
    progress = _progress(project, records, _current_phase(records, phase))
    if progress.current != "verify":
        return None
    return "reviewer" if progress.reason == "integration-report" else progress.reason


def _land_stage(project: Project, records: list[Record], phase: str) -> str | None:
    progress = _progress(project, records, _current_phase(records, phase))
    match progress.current:
        case "land":
            if progress.reason != "failed-landing":
                return "land"
            config = load_project_config(project.project_root)
            return "repair-ci" if config.land_adapter == "github-pr" else "land"
        case "close":
            return "close"
        case _:
            return None


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


def _constraints_section(records: list[Record], areas: Sequence[str]) -> str:
    entries: list[str] = []
    seen: set[str] = set()
    for area in dict.fromkeys(areas):
        found = applicable(records, area)
        if not found:
            entries.append(f"No standing constraints for area `{area}`.")
        for constraint in found:
            if constraint.id in seen:
                continue
            seen.add(constraint.id)
            entries.append(
                f"### {constraint.name}\n"
                f"**area**: {constraint.area}; **version**: {constraint.id}\n\n"
                f"**rule**: {constraint.rule}\n\n"
                f"**basis**: {constraint.basis}"
            )
    if not areas:
        known = declared_areas(records)
        if known:
            entries.append(
                "No `--area` given, so no standing constraints are listed. "
                f"Areas with constraints: {', '.join(known)}."
            )
    if not entries:
        return ""
    return "## Applicable standing constraints\n\n" + "\n\n".join(entries)


def phase_step_action(
    project: Project, phase: str, step: Step, areas: Sequence[str] = ()
) -> RunAction:
    records = project.records()
    current = _current_phase(records, phase)
    action = _action_for(project, records, current, step, _progress(project, records, current))
    action = _with_brief(project, action)
    if step == "design" and action.state == "ready":
        section = _constraints_section(records, areas)
        if section:
            action = replace(action, brief=f"{action.brief.rstrip()}\n\n{section}\n")
    return action


def _all_actions(
    project: Project, records: list[Record], run: Record, *, with_brief: bool
) -> tuple[RunAction, ...]:
    steps = _run_steps(run)
    phases = _phase_records(records, run)
    actions: list[RunAction] = []
    prepare_barrier = _text(run, "operation") == "prepare"
    selected_phases = {phase.subject for phase in phases}
    progress = {phase.subject: _progress(project, records, phase) for phase in phases}
    specs_complete = all(_stage_done(item, "spec") for item in progress.values())
    for phase in phases:
        for step in steps:
            if _stage_done(progress[phase.subject], step):
                continue
            if prepare_barrier and step == "design" and not specs_complete:
                break
            action = _action_for(
                project,
                records,
                phase,
                step,
                progress[phase.subject],
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
