"""Handlers for `orchestra wave` and `orchestra task`."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from orchestra.canon.errors import StaleWriteError, StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.types import Record
from orchestra.canon.workspace import Access
from orchestra.conductor import land_task, task_redispatch, wave
from orchestra.conductor.cli.options import open_project, work_dir
from orchestra.conductor.evidence import EVIDENCE_SCHEMA, EvidenceError
from orchestra.conductor.redispatch_facts import redispatch_facts
from orchestra.conductor.task_landing import land_and_close
from orchestra.score.planning.work_item import WorkItemShapeError
from orchestra.tools.command_kit import Command, CommandError, emit_json, fail
from orchestra.tools.git import Git

BriefRenderer = Callable[[str, list[Record]], str]


def _wave_start(args: argparse.Namespace, render_brief: BriefRenderer) -> int:
    start = work_dir(args)
    project = open_project(args, start, Access.WRITE)
    try:
        repo = Git(start).primary_checkout()
        result = wave.start(project, repo, args.phase, Git(start).root())
        records = project.records()
        briefs = {t.task: render_brief(t.task, records) for t in result.tasks}
    except (wave.WaveError, OSError, RuntimeError, StoreBindingError, StoreError) as exc:
        raise CommandError(f"{args.phase}: {exc}") from exc
    if args.json:
        if result.runner is not None:
            emit_json(
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
        emit_json(
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
    start = work_dir(args)
    project = open_project(args, start, Access.WRITE)
    try:
        result = wave.end(project, Git(start).primary_checkout(), args.phase)
    except (wave.WaveError, OSError, RuntimeError, StoreBindingError, StoreError) as exc:
        raise CommandError(f"{args.phase}: {exc}") from exc
    if args.json:
        emit_json(
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
    start = work_dir(args)
    project = open_project(args, start, Access.WRITE)
    try:
        result = wave.resolve(project, Git(start).primary_checkout(), args.phase, args.task)
    except (wave.WaveError, OSError, RuntimeError, StoreBindingError, StoreError) as exc:
        raise CommandError(f"{args.phase}: {exc}") from exc
    if args.json:
        emit_json(
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
        fail(args, f"{args.phase}: {reason}")
    return result.exit_code


def _task_land(args: argparse.Namespace) -> int:
    if args.schema:
        emit_json(EVIDENCE_SCHEMA)
        return 0
    if not args.task or not args.evidence:
        raise CommandError("a task and --evidence are required")
    start = work_dir(args)
    project = open_project(args, start, Access.WRITE)
    try:
        repo = Git(start).primary_checkout()
        landing = land_and_close(project, repo, args.task, Path(args.evidence))
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
        raise CommandError(f"{args.task}: {exc}") from exc
    landed, closure = landing.landed, landing.closure
    if args.json:
        emit_json(
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
    start = work_dir(args)
    project = open_project(args, start, Access.WRITE)
    try:
        record = task_redispatch.redispatch(
            project, args.task, expected_revision=args.expected_revision
        )
    except (
        StaleWriteError,
        task_redispatch.RedispatchError,
        OSError,
        RuntimeError,
        StoreBindingError,
        StoreError,
    ) as exc:
        raise CommandError(f"{args.task}: {exc}") from exc
    facts = redispatch_facts(record)
    if args.json:
        emit_json(
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


def _configure_wave_start(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("phase", help="Phase slug")
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument("--cwd", default=None, help="Directory inside the repo (default: cwd)")
    parser.add_argument("--store", default=None, metavar="DIR", help="Store repo root")


def _configure_wave_resolve(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("phase", help="Phase slug")
    parser.add_argument("task", help="Task slug whose merge conflicted")
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument("--cwd", default=None, help="Directory inside the repo (default: cwd)")
    parser.add_argument("--store", default=None, metavar="DIR", help="Store repo root")


def _configure_task_redispatch(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("task", help="Work-item subject")
    parser.add_argument(
        "--expected-revision", required=True, help="Exact current work-item revision"
    )
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument("--cwd", default=None, help="Directory inside the repo (default: cwd)")
    parser.add_argument("--store", default=None, metavar="DIR", help="Store repo root")


def _configure_task_land(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("task", nargs="?", help="Work-item subject")
    parser.add_argument("--evidence", default=None, help="Evidence JSON file")
    parser.add_argument("--schema", action="store_true", help="Print the evidence JSON schema")
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument("--cwd", default=None, help="Directory inside the repo (default: cwd)")
    parser.add_argument("--store", default=None, metavar="DIR", help="Store repo root")


def commands(render_brief: BriefRenderer) -> list[Command]:
    return [
        Command(
            "wave",
            "Start and end the waves of a phase",
            children=(
                Command(
                    "start",
                    "Cut task branches and worktrees for the next ready wave and mark it "
                    "in progress",
                    configure=_configure_wave_start,
                    handle=lambda args: _wave_start(args, render_brief),
                ),
                Command(
                    "end",
                    "Merge each passing task branch into the phase branch in task-slug order",
                    configure=_configure_wave_start,
                    handle=_wave_end,
                ),
                Command(
                    "resolve",
                    "Finish a conflicted task merge once both tasks' work is kept",
                    configure=_configure_wave_resolve,
                    handle=_wave_resolve,
                ),
            ),
        ),
        Command(
            "task",
            "Manage one task",
            children=(
                Command(
                    "redispatch",
                    "Start a new measured dispatch for an in-progress task",
                    configure=_configure_task_redispatch,
                    handle=_task_redispatch,
                ),
                Command(
                    "land",
                    "Commit a task worktree, record its evidence, run its checks, close it",
                    configure=_configure_task_land,
                    handle=_task_land,
                ),
            ),
        ),
    ]
