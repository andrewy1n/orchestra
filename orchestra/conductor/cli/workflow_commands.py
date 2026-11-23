"""Parsers and handlers for `orchestra workflow`."""

from __future__ import annotations

import argparse

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project, StoreBindingError
from orchestra.canon.validation import ValidationError
from orchestra.canon.workspace import Access
from orchestra.conductor.briefs.render import render_skill_brief
from orchestra.conductor.cli.options import open_project, work_dir
from orchestra.conductor.phases.workflow.run_record import resolve_run
from orchestra.conductor.phases.workflow.workflow import (
    RunAction,
    RunPreview,
    WorkflowRunError,
    next_actions,
    phase_step_action,
    preview_run,
    run_status,
    start_previewed_run,
)
from orchestra.conductor.phases.workflow.workflow_review import (
    WorkflowReviewError,
    record_step_review,
)
from orchestra.conductor.verification.evidence.acceptance_amendment import (
    ROUTINE_CHECKS,
    amend_acceptance,
)
from orchestra.score.lookups import current_phase, dependencies
from orchestra.score.workflow.workflow_reviews import Authority, Step
from orchestra.tools.command_kit import Command, CommandError, emit_json


def _add_read_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument("--cwd", default=None, help="Directory used to resolve the store")
    parser.add_argument("--store", default=None, metavar="DIR", help="Store repo root")


def _configure_preview(command: argparse.ArgumentParser) -> None:
    command.add_argument("effort", help="Effort slug")
    command.add_argument("selector", help="Phase slug, ordinal, range, or comma-separated list")
    command.add_argument(
        "operation",
        choices=(
            "phase",
            "prepare",
            "deliver",
            "spec",
            "design",
            "tasks",
            "execute",
            "verify",
            "land",
        ),
        help="Built-in playbook or one workflow step",
    )
    command.add_argument("--json", action="store_true", help="Print one JSON object")
    command.add_argument("--cwd", default=None, help="Directory used to resolve the store")
    command.add_argument("--store", default=None, metavar="DIR", help="Store repo root")


def _configure_start(command: argparse.ArgumentParser) -> None:
    _configure_preview(command)
    command.add_argument(
        "--snapshot-token",
        required=True,
        help="Snapshot token from a prior workflow preview",
    )


def _configure_status(status: argparse.ArgumentParser) -> None:
    status.add_argument("run", help="Run subject or record id")
    _add_read_options(status)


def _configure_next(next_parser: argparse.ArgumentParser) -> None:
    next_parser.add_argument("run", help="Run subject or record id")
    next_parser.add_argument(
        "--no-brief", action="store_true", help="Omit the step brief from ready actions"
    )
    _add_read_options(next_parser)


def _configure_brief(brief: argparse.ArgumentParser) -> None:
    brief.description = (
        "Print the brief for one phase step. The brief equals the next brief for the same "
        "store state, except in a prepare run, whose barrier next applies and brief does not."
    )
    brief.add_argument("phase", nargs="?", help="Phase slug")
    brief.add_argument(
        "step",
        nargs="?",
        choices=("spec", "design", "tasks", "execute", "verify", "land"),
    )
    brief.add_argument("--skill", help="Print the brief for a skill instead of a phase step")
    _add_read_options(brief)


def _configure_review(review: argparse.ArgumentParser) -> None:
    review.add_argument("phase", help="Phase slug")
    review.add_argument("step", choices=("spec", "design", "tasks", "execute", "verify"))
    review.add_argument("--artifact", required=True, help="Reviewed artifact record id")
    review.add_argument(
        "--authority",
        required=True,
        choices=("user-approval", "explicit-delegation", "task-plan-policy"),
    )
    review.add_argument("--basis", required=True, help="Approval or review basis")
    _add_read_options(review)


def _configure_amend(amend: argparse.ArgumentParser) -> None:
    amend.add_argument("acceptance", help="Active acceptance record id")
    amend.add_argument("--expected-revision", required=True, help="Exact acceptance revision")
    amend.add_argument("--basis", required=True, help="Reason and evidence for the change")
    changes = amend.add_mutually_exclusive_group(required=True)
    changes.add_argument("--equivalent-command", help="Command that runs the same checks")
    changes.add_argument("--routine-check", choices=ROUTINE_CHECKS, help="Change TDD to check")
    _add_read_options(amend)


def _step(operation: str) -> Step | None:
    match operation:
        case "spec" | "design" | "tasks" | "execute" | "verify" | "land":
            return operation
        case _:
            return None


def _preview(project: Project, args: argparse.Namespace) -> RunPreview:
    step = _step(args.operation)
    operation = "single-step" if step is not None else args.operation
    return preview_run(project, args.effort, args.selector, operation, step=step)


def _preview_json(project: Project, preview: RunPreview) -> dict[str, object]:
    records = project.records()
    prerequisites: dict[str, list[str]] = {}
    for phase in preview.phases:
        record = current_phase(phase, records)
        if record is None:
            raise WorkflowRunError(f"phase disappeared from the store: {phase}")
        prerequisites[phase] = dependencies(record)
    return {
        "effort": preview.effort,
        "operation": preview.operation,
        "phases": list(preview.phases),
        "requested_steps": list(preview.requested_steps),
        "prerequisites": prerequisites,
        "external_dependencies": list(preview.external_dependencies),
        "snapshot_token": preview.change_token,
        "definition_version": "1",
    }


def _action_json(action: RunAction, *, with_brief: bool = True) -> dict[str, str]:
    output = {
        "phase": action.phase,
        "step": action.step,
        "state": action.state,
        "reason": action.reason,
    }
    if with_brief and action.state == "ready":
        output["brief"] = action.brief
    return output


def _open(args: argparse.Namespace, access: Access) -> Project:
    return open_project(args, work_dir(args), access)


def _preview_command(args: argparse.Namespace) -> int:
    project = _open(args, Access.READ)
    try:
        preview = _preview(project, args)
        output = _preview_json(project, preview)
    except (OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        raise CommandError(f"{args.effort}: {exc}") from exc
    if args.json:
        emit_json(output)
    else:
        print(f"{preview.operation}: {', '.join(preview.phases)}")
        print(f"steps: {', '.join(preview.requested_steps)}")
        print(f"snapshot: {preview.change_token}")
    return 0


def _start_command(args: argparse.Namespace) -> int:
    project = _open(args, Access.WRITE)
    try:
        preview = _preview(project, args)
        run = start_previewed_run(project, preview, args.snapshot_token)
        output = {"preview": _preview_json(project, preview), "run": run}
    except (OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        raise CommandError(f"{args.effort}: {exc}") from exc
    if args.json:
        emit_json(output)
    else:
        print(f"started {run['subject']}: {', '.join(preview.phases)}")
    return 0


def _status_command(args: argparse.Namespace, *, actions_only: bool) -> int:
    project = _open(args, Access.READ)
    with_brief = actions_only and not args.no_brief
    try:
        if actions_only:
            run = resolve_run(project, args.run)
            run_actions = next_actions(project, args.run)
            output: dict[str, object] = {
                "run": run,
                "actions": [_action_json(action, with_brief=with_brief) for action in run_actions],
            }
        else:
            status = run_status(project, args.run)
            run_actions = status.actions
            output = {
                "run": status.run,
                "status": "complete" if status.complete else "incomplete",
                "complete": status.complete,
                "incomplete": status.incomplete,
                "actions": [
                    _action_json(action, with_brief=with_brief) for action in status.actions
                ],
            }
    except (
        OSError,
        RuntimeError,
        StoreBindingError,
        StoreError,
        WorkflowRunError,
        ValueError,
    ) as exc:
        raise CommandError(f"{args.run}: {exc}") from exc
    if args.json:
        emit_json(output)
    else:
        print(f"{output.get('status', 'next')}: {args.run}")
        for action in run_actions:
            print(f"{action.phase} {action.step}: {action.state} {action.reason}")
    return 0


def _status(args: argparse.Namespace) -> int:
    return _status_command(args, actions_only=False)


def _next(args: argparse.Namespace) -> int:
    return _status_command(args, actions_only=True)


def _brief(args: argparse.Namespace) -> int:
    if args.skill is not None:
        return _skill_brief_command(args)
    if args.phase is None or args.step is None:
        raise CommandError("arguments: give --skill or both phase and step")
    project = _open(args, Access.READ)
    try:
        action = phase_step_action(project, args.phase, args.step)
    except (
        OSError,
        RuntimeError,
        StoreBindingError,
        StoreError,
        WorkflowRunError,
        ValueError,
    ) as exc:
        raise CommandError(f"{args.phase}: {exc}") from exc
    if action.state != "ready":
        raise CommandError(f"{args.phase}: {action.reason}")
    if args.json:
        emit_json(_action_json(action))
    else:
        print(action.brief)
    return 0


def _review(args: argparse.Namespace) -> int:
    project = _open(args, Access.WRITE)
    step = _step(args.step)
    if step is None:
        raise CommandError(f"{args.phase}: unsupported workflow step")
    authority: Authority = args.authority
    try:
        artifact = project.get(args.artifact)
        review = record_step_review(
            project,
            phase=args.phase,
            step=step,
            artifact=artifact,
            authority=authority,
            basis=args.basis,
        )
    except (
        OSError,
        RuntimeError,
        StoreBindingError,
        StoreError,
        WorkflowReviewError,
        ValueError,
    ) as exc:
        raise CommandError(f"{args.phase}: {exc}") from exc
    output = {"review": review}
    if args.json:
        emit_json(output)
    else:
        print(f"{review['subject']}: reviewed {step}")
    return 0


def _skill_brief_command(args: argparse.Namespace) -> int:
    if args.phase is not None or args.step is not None:
        raise CommandError("--skill: takes no phase or step")
    try:
        text = render_skill_brief(args.skill)
    except ValueError as exc:
        raise CommandError(f"{args.skill}: {exc}") from exc
    if args.json:
        emit_json({"skill": args.skill, "brief": text})
        return 0
    print(text)
    return 0


def _amend(args: argparse.Namespace) -> int:
    project = _open(args, Access.WRITE)
    try:
        record = amend_acceptance(
            project,
            args.acceptance,
            expected_revision=args.expected_revision,
            basis=args.basis,
            equivalent_command=args.equivalent_command,
            routine_check=args.routine_check,
        )
    except (OSError, RuntimeError, StoreError, ValidationError, ValueError) as exc:
        raise CommandError(f"{args.acceptance}: {exc}") from exc
    if args.json:
        emit_json(record)
    else:
        print(record["id"])
    return 0


def commands() -> list[Command]:
    return [
        Command(
            "workflow",
            "Preview and resume built-in workflow playbooks",
            children=(
                Command(
                    "preview",
                    "Preview a selected workflow",
                    configure=_configure_preview,
                    handle=_preview_command,
                ),
                Command(
                    "start",
                    "Start a selected workflow",
                    configure=_configure_start,
                    handle=_start_command,
                ),
                Command(
                    "status",
                    "Show current run progress",
                    configure=_configure_status,
                    handle=_status,
                ),
                Command(
                    "next",
                    "Show safe next actions for a run",
                    configure=_configure_next,
                    handle=_next,
                ),
                Command(
                    "brief",
                    "Print the brief for one phase step",
                    configure=_configure_brief,
                    handle=_brief,
                ),
                Command(
                    "review",
                    "Record a workflow step review",
                    configure=_configure_review,
                    handle=_review,
                ),
                Command(
                    "amend-check",
                    "Apply a parent-approved verification change",
                    configure=_configure_amend,
                    handle=_amend,
                ),
            ),
        )
    ]
