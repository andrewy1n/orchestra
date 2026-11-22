"""Handlers for `orchestra wave` and `orchestra task`."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from orchestra.canon.errors import StaleWriteError, StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.types import Record
from orchestra.canon.workspace import Access, StoreNotReady
from orchestra.conductor import land_task, task_redispatch, wave
from orchestra.conductor.cli.workspace import (
    command_dir,
    not_ready_message,
    print_json,
    resolve_workspace,
)
from orchestra.conductor.evidence import EVIDENCE_SCHEMA, EvidenceError
from orchestra.conductor.redispatch_facts import redispatch_facts
from orchestra.conductor.task_landing import land_and_close
from orchestra.score.work_item import WorkItemShapeError
from orchestra.tools.git import Git

BriefRenderer = Callable[[str, list[Record]], str]


def run_wave(args: argparse.Namespace) -> int:
    if args.action == "start":
        return _wave_start(args)
    if args.action == "resolve":
        return _wave_resolve(args)
    return _wave_end(args)


def run_task(args: argparse.Namespace) -> int:
    if args.action == "redispatch":
        return _task_redispatch(args)
    return _task_land(args)


def _wave_start(args: argparse.Namespace) -> int:
    render_brief: BriefRenderer = args.render_brief
    start = command_dir(args)
    try:
        workspace = resolve_workspace(args.store, start, Access.WRITE)
        project = workspace.open()
        repo = Git(start).primary_checkout()
        result = wave.start(project, repo, args.phase, Git(start).root())
        records = project.records()
        briefs = {t.task: render_brief(t.task, records) for t in result.tasks}
    except StoreNotReady as exc:
        print(
            f"orchestra wave start: {args.phase}: {not_ready_message(exc, start)}", file=sys.stderr
        )
        return 2
    except (wave.WaveError, OSError, RuntimeError, StoreBindingError, StoreError) as exc:
        print(f"orchestra wave start: {args.phase}: {exc}", file=sys.stderr)
        return 2
    if args.json:
        if result.runner is not None:
            print_json(
                {
                    "phase": result.phase,
                    "wave": result.wave,
                    "execution_mode": result.execution_mode,
                    "task": result.runner.task,
                    "state": result.runner.state,
                    "execution_report": result.runner.report_id,
                    "checks": list(result.runner.checks),
                    "refusal_reasons": list(result.runner.refusal_reasons),
                }
            )
            return result.exit_code
        print_json(
            {
                "phase": result.phase,
                "wave": result.wave,
                "execution_mode": result.execution_mode,
                "tasks": [
                    {
                        "task": t.task,
                        "executor": t.executor,
                        "write_root": t.write_root,
                        "branch": t.branch,
                        "brief": briefs[t.task],
                    }
                    for t in result.tasks
                ],
            }
        )
        return 0
    if result.runner is not None:
        print(f"## {result.runner.task} ({result.runner.state})")
        for check in result.runner.checks:
            print(f"{check['subject']}: exit {check['exit_code']} {check['message']}")
        for reason in result.runner.refusal_reasons:
            print(reason)
        return result.exit_code
    for t in result.tasks:
        print(f"## {t.task} ({t.executor}) {t.write_root}\n")
        print(briefs[t.task])
    return 0


def _wave_end(args: argparse.Namespace) -> int:
    start = command_dir(args)
    try:
        workspace = resolve_workspace(args.store, start, Access.WRITE)
        result = wave.end(workspace.open(), Git(start).primary_checkout(), args.phase)
    except StoreNotReady as exc:
        print(f"orchestra wave end: {args.phase}: {not_ready_message(exc, start)}", file=sys.stderr)
        return 2
    except (wave.WaveError, OSError, RuntimeError, StoreBindingError, StoreError) as exc:
        print(f"orchestra wave end: {args.phase}: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print_json(
            {
                "phase": result.phase,
                "merged": list(result.merged),
                "skipped": [{"task": t, "reason": why} for t, why in result.skipped],
                "conflict": result.conflict,
                "question": result.question_id,
            }
        )
    else:
        for task_slug in result.merged:
            print(f"merged task/{result.phase}/{task_slug}")
        for task_slug, why in result.skipped:
            print(f"skipped {task_slug}: {why}")
        if result.conflict:
            print(f"conflict merging {result.conflict}; question {result.question_id}")
    return result.exit_code


def _wave_resolve(args: argparse.Namespace) -> int:
    start = command_dir(args)
    try:
        workspace = resolve_workspace(args.store, start, Access.WRITE)
        result = wave.resolve(
            workspace.open(), Git(start).primary_checkout(), args.phase, args.task
        )
    except StoreNotReady as exc:
        print(
            f"orchestra wave resolve: {args.phase}: {not_ready_message(exc, start)}",
            file=sys.stderr,
        )
        return 2
    except (wave.WaveError, OSError, RuntimeError, StoreBindingError, StoreError) as exc:
        print(f"orchestra wave resolve: {args.phase}: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print_json(
            {
                "phase": result.phase,
                "task": result.task,
                "ready": result.ready,
                "refusals": list(result.refusals),
                "commit": result.commit,
            }
        )
    elif result.ready:
        print(f"resolved {result.task}: merge commit {result.commit}")
    for reason in result.refusals:
        print(f"orchestra wave resolve: {args.phase}: {reason}", file=sys.stderr)
    return result.exit_code


def _task_land(args: argparse.Namespace) -> int:
    if args.schema:
        print_json(EVIDENCE_SCHEMA)
        return 0
    if not args.task or not args.evidence:
        print("orchestra task land: a task and --evidence are required", file=sys.stderr)
        return 2
    start = command_dir(args)
    try:
        workspace = resolve_workspace(args.store, start, Access.WRITE)
        repo = Git(start).primary_checkout()
        landing = land_and_close(workspace.open(), repo, args.task, Path(args.evidence))
    except StoreNotReady as exc:
        print(f"orchestra task land: {args.task}: {not_ready_message(exc, start)}", file=sys.stderr)
        return 2
    except (
        EvidenceError,
        land_task.LandError,
        wave.WaveError,
        OSError,
        RuntimeError,
        StoreBindingError,
        StoreError,
        WorkItemShapeError,
    ) as exc:
        print(f"orchestra task land: {args.task}: {exc}", file=sys.stderr)
        return 2
    landed, closure = landing.landed, landing.closure
    if args.json:
        print_json(
            {
                "task": landed.task,
                "commit": landed.commit,
                "revision": landed.revision,
                "execution_report": landed.report_id,
                "check_runs": [c.check_run_id for c in landed.checks],
                "state": closure.state,
                "reasons": list(closure.reasons),
                "question": closure.question_id,
            }
        )
    else:
        print(
            f"{landed.task}: {closure.state} (report {landed.report_id}, "
            f"revision {landed.revision})"
        )
        for reason in closure.reasons:
            print(f"  {reason}", file=sys.stderr)
    return closure.code


def _task_redispatch(args: argparse.Namespace) -> int:
    start = command_dir(args)
    try:
        workspace = resolve_workspace(args.store, start, Access.WRITE)
        record = task_redispatch.redispatch(
            workspace.open(), args.task, expected_revision=args.expected_revision
        )
    except StoreNotReady as exc:
        print(
            f"orchestra task redispatch: {args.task}: {not_ready_message(exc, start)}",
            file=sys.stderr,
        )
        return 2
    except (
        StaleWriteError,
        task_redispatch.RedispatchError,
        OSError,
        RuntimeError,
        StoreBindingError,
        StoreError,
    ) as exc:
        print(f"orchestra task redispatch: {args.task}: {exc}", file=sys.stderr)
        return 2
    facts = redispatch_facts(record)
    if args.json:
        print_json(
            {
                "task": facts.task,
                "revision": facts.revision,
                "attempts": facts.attempts,
                "dispatch_id": facts.dispatch_id,
                "dispatch_started_at": facts.dispatch_started_at,
                "assignee": facts.assignee,
                "write_root": facts.write_root,
            }
        )
    else:
        print(f"redispatched {facts.task} (attempt {facts.attempts})")
    return 0
