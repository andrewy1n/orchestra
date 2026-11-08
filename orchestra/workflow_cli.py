from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from orchestra.canon.errors import StaleWriteError, StoreError
from orchestra.canon.project import Project, StoreBindingError
from orchestra.conductor.workflow import (
    RunAction,
    RunPreview,
    WorkflowRunError,
    next_actions,
    preview_run,
    run_status,
    start_run,
)
from orchestra.conductor.workflow_review import WorkflowReviewError, record_step_review
from orchestra.score.workflow_reviews import Authority, Step
from orchestra.store import resolve_location


def add_parser(parser: argparse.ArgumentParser) -> None:
    actions = parser.add_subparsers(dest="action", required=True)

    for action in ("preview", "start"):
        command = actions.add_parser(action, help=f"{action.capitalize()} a selected workflow")
        command.add_argument("effort", help="Effort slug")
        command.add_argument("selector", help="Phase slug, ordinal, range, or comma-separated list")
        command.add_argument(
            "operation",
            choices=("phase", "prepare", "deliver", "spec", "design", "tasks", "execute", "verify"),
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
    _add_read_options(next_parser)

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


def _add_read_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument("--cwd", default=None, help="Directory used to resolve the store")
    parser.add_argument("--store", default=None, metavar="DIR", help="Store repo root")


def _project(args: argparse.Namespace) -> Project:
    cwd = Path(args.cwd).expanduser() if args.cwd else Path.cwd()
    return resolve_location(args.store, cwd).open()


def _step(operation: str) -> Step | None:
    match operation:
        case "spec" | "design" | "tasks" | "execute" | "verify":
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
        record = next(
            (
                item
                for item in records
                if item["record_type"] == "score:phase" and item["subject"] == phase
            ),
            None,
        )
        if record is None:
            raise WorkflowRunError(f"phase disappeared from the store: {phase}")
        raw = record["payload"].get("depends_on", [])
        prerequisites[phase] = (
            [item for item in raw if isinstance(item, str)] if isinstance(raw, list) else []
        )
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


def _action_json(action: RunAction) -> dict[str, str]:
    return {
        "phase": action.phase,
        "step": action.step,
        "state": action.state,
        "reason": action.reason,
    }


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
        if preview.change_token != args.snapshot_token:
            raise StaleWriteError("snapshot changed; preview again before starting")
        run = start_run(project, preview)
        output = {"preview": _preview_json(project, preview), "run": run}
    except (OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        return _fail("start", args.effort, exc)
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print(f"started {run['subject']}: {', '.join(preview.phases)}")
    return 0


def _status_command(project: Project, args: argparse.Namespace, *, actions_only: bool) -> int:
    try:
        if actions_only:
            run = project.resolve("score:run", args.run)
            run_actions = next_actions(project, args.run)
            output: dict[str, object] = {
                "run": run,
                "actions": [_action_json(action) for action in run_actions],
            }
        else:
            status = run_status(project, args.run)
            run_actions = status.actions
            output = {
                "run": status.run,
                "status": "complete" if status.complete else "incomplete",
                "complete": status.complete,
                "incomplete": status.incomplete,
                "actions": [_action_json(action) for action in status.actions],
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


def run(args: argparse.Namespace) -> int:
    try:
        project = _project(args)
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
    return _review_command(project, args)
