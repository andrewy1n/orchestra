"""Parsers and handlers for `orchestra workflow`."""

from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project, StoreBindingError
from orchestra.canon.validation import ValidationError
from orchestra.canon.workspace import Access, StoreNotReady
from orchestra.conductor.acceptance_amendment import ROUTINE_CHECKS, amend_acceptance
from orchestra.conductor.briefs.render import render_skill_brief
from orchestra.conductor.cli.workspace import command_dir, not_ready_message, resolve_workspace
from orchestra.conductor.run_record import resolve_run
from orchestra.conductor.workflow import (
    RunAction,
    RunPreview,
    WorkflowRunError,
    next_actions,
    phase_step_action,
    preview_run,
    run_status,
    start_previewed_run,
)
from orchestra.conductor.workflow_review import WorkflowReviewError, record_step_review
from orchestra.score.lookups import current_phase, dependencies
from orchestra.score.workflow_reviews import Authority, Step

if TYPE_CHECKING:
    from orchestra.conductor.cli.parsers import SubparserGroup


def add_workflow_parser(sub: SubparserGroup) -> None:
    parser = sub.add_parser("workflow", help="Preview and resume built-in workflow playbooks")
    actions = parser.add_subparsers(dest="action", required=True)

    for action in ("preview", "start"):
        command = actions.add_parser(action, help=f"{action.capitalize()} a selected workflow")
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
        if action == "start":
            command.add_argument(
                "--snapshot-token",
                required=True,
                help="Snapshot token from a prior workflow preview",
            )

    status = actions.add_parser("status", help="Show current run progress")
    status.add_argument("run", help="Run subject or record id")
    _add_read_options(status)

    next_parser = actions.add_parser("next", help="Show safe next actions for a run")
    next_parser.add_argument("run", help="Run subject or record id")
    next_parser.add_argument(
        "--no-brief", action="store_true", help="Omit the step brief from ready actions"
    )
    _add_read_options(next_parser)

    brief = actions.add_parser(
        "brief",
        help="Print the brief for one phase step",
        description=(
            "Print the brief for one phase step. The brief equals the next brief for the same "
            "store state, except in a prepare run, whose barrier next applies and brief does not."
        ),
    )
    brief.add_argument("phase", nargs="?", help="Phase slug")
    brief.add_argument(
        "step",
        nargs="?",
        choices=("spec", "design", "tasks", "execute", "verify", "land"),
    )
    brief.add_argument("--skill", help="Print the brief for a skill instead of a phase step")
    _add_read_options(brief)

    review = actions.add_parser("review", help="Record a workflow step review")
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

    amend = actions.add_parser("amend-check", help="Apply a parent-approved verification change")
    amend.add_argument("acceptance", help="Active acceptance record id")
    amend.add_argument("--expected-revision", required=True, help="Exact acceptance revision")
    amend.add_argument("--basis", required=True, help="Reason and evidence for the change")
    changes = amend.add_mutually_exclusive_group(required=True)
    changes.add_argument("--equivalent-command", help="Command that runs the same checks")
    changes.add_argument("--routine-check", choices=ROUTINE_CHECKS, help="Change TDD to check")
    _add_read_options(amend)


def _add_read_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument("--cwd", default=None, help="Directory used to resolve the store")
    parser.add_argument("--store", default=None, metavar="DIR", help="Store repo root")


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


def _fail(action: str, subject: str, error: Exception) -> int:
    print(f"orchestra workflow {action}: {subject}: {error}", file=sys.stderr)
    return 2


def _preview_command(project: Project, args: argparse.Namespace) -> int:
    try:
        preview = _preview(project, args)
        output = _preview_json(project, preview)
    except (OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        return _fail("preview", args.effort, exc)
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"{preview.operation}: {', '.join(preview.phases)}")
        print(f"steps: {', '.join(preview.requested_steps)}")
        print(f"snapshot: {preview.change_token}")
    return 0


def _start_command(project: Project, args: argparse.Namespace) -> int:
    try:
        preview = _preview(project, args)
        run = start_previewed_run(project, preview, args.snapshot_token)
        output = {"preview": _preview_json(project, preview), "run": run}
    except (OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        return _fail("start", args.effort, exc)
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"started {run['subject']}: {', '.join(preview.phases)}")
    return 0


def _status_command(project: Project, args: argparse.Namespace, *, actions_only: bool) -> int:
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
        return _fail("next" if actions_only else "status", args.run, exc)
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"{output.get('status', 'next')}: {args.run}")
        for action in run_actions:
            print(f"{action.phase} {action.step}: {action.state} {action.reason}")
    return 0


def _brief_command(project: Project, args: argparse.Namespace) -> int:
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
        return _fail("brief", args.phase, exc)
    if action.state != "ready":
        return _fail("brief", args.phase, WorkflowRunError(action.reason))
    if args.json:
        print(json.dumps(_action_json(action), indent=2))
    else:
        print(action.brief)
    return 0


def _review_command(project: Project, args: argparse.Namespace) -> int:
    step = _step(args.step)
    if step is None:
        return _fail("review", args.phase, WorkflowReviewError("unsupported workflow step"))
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
        return _fail("review", args.phase, exc)
    output = {"review": review}
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"{review['subject']}: reviewed {step}")
    return 0


def _skill_brief_command(args: argparse.Namespace) -> int:
    if args.phase is not None or args.step is not None:
        return _fail("brief", "--skill", ValueError("takes no phase or step"))
    try:
        text = render_skill_brief(args.skill)
    except ValueError as exc:
        return _fail("brief", args.skill, exc)
    if args.json:
        print(json.dumps({"skill": args.skill, "brief": text}, indent=2))
        return 0
    print(text)
    return 0


def _access(action: str) -> Access:
    if action in ("start", "review", "amend-check"):
        return Access.WRITE
    return Access.READ


def _subject(args: argparse.Namespace) -> str:
    match args.action:
        case "preview" | "start":
            return args.effort
        case "status" | "next":
            return args.run
        case "brief" | "review":
            return args.phase or "arguments"
        case _:
            return args.acceptance


def run_workflow(args: argparse.Namespace) -> int:
    if args.action == "brief":
        if args.skill is not None:
            return _skill_brief_command(args)
        if args.phase is None or args.step is None:
            return _fail("brief", "arguments", ValueError("give --skill or both phase and step"))
    start = command_dir(args)
    try:
        project = resolve_workspace(args.store, start, _access(args.action)).open()
    except StoreNotReady as exc:
        print(
            f"orchestra workflow {args.action}: {_subject(args)}: {not_ready_message(exc, start)}",
            file=sys.stderr,
        )
        return 2
    except (OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        return _fail(args.action, "store", exc)
    if args.action == "preview":
        return _preview_command(project, args)
    if args.action == "start":
        return _start_command(project, args)
    if args.action == "status":
        return _status_command(project, args, actions_only=False)
    if args.action == "next":
        return _status_command(project, args, actions_only=True)
    if args.action == "brief":
        return _brief_command(project, args)
    if args.action == "amend-check":
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
            return _fail(args.action, args.acceptance, exc)
        print(json.dumps(record, indent=2) if args.json else record["id"])
        return 0
    return _review_command(project, args)
