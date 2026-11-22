"""Handlers for `orchestra suite`."""

from __future__ import annotations

import argparse
import sys

from orchestra.canon.project import StoreBindingError
from orchestra.canon.workspace import Access
from orchestra.conductor import suite
from orchestra.conductor.cli.options import open_project, work_dir
from orchestra.tools.command_kit import Command, CommandError, emit_json, fail

_FAILURES = (OSError, RuntimeError, StoreBindingError, ValueError)


def _policy_document(policy: suite.SuitePolicy) -> dict[str, object]:
    return {
        "mode": policy.mode,
        "command": policy.command,
        "gate": policy.gate,
        "source_path": policy.source_path,
        "run_locally": policy.run_locally,
        "blocks_merge": policy.blocks_merge,
        "advisory": policy.advisory,
        "deferred_landing_stop": policy.deferred_landing_stop,
        "create_fix_tasks_on_fail": policy.create_fix_tasks_on_fail,
    }


def _result_document(result: suite.SuiteResult) -> dict[str, object]:
    return {
        "state": result.result,
        "result": result.result,
        "revision": result.revision,
        "exit_code": result.exit_code,
        "duration_s": result.duration_s,
        "output_sha256": result.output_sha256,
        "failing_node_ids": result.failing_node_ids,
        "diff_sha256": result.diff_sha256,
        "refuse": result.refuse,
        "refuse_message": result.refuse_message,
        "skipped": result.skipped,
        "skip_reason": result.skip_reason,
        "run_id": result.run_id,
        "reason": result.reason,
    }


def _job(args: argparse.Namespace) -> suite.SuiteStart:
    return suite.load_suite_job(
        worktree=work_dir(args),
        phase_slug=args.phase,
        session_name=args.session,
        run_id=getattr(args, "run_id", None),
    )


def _policy(args: argparse.Namespace) -> int:
    try:
        policy = suite.load_suite_policy(work_dir(args))
    except _FAILURES as exc:
        raise CommandError(str(exc)) from exc
    emit_json(_policy_document(policy))
    return 0


def _start(args: argparse.Namespace) -> int:
    try:
        outcome = suite.start_suite_background(
            worktree=work_dir(args),
            phase_slug=args.phase,
            phase_head=args.phase_head,
            session_name=args.session,
            suite_command=args.suite_command,
            allow_dirty=args.allow_dirty,
            timeout=args.timeout,
        )
    except _FAILURES as exc:
        raise CommandError(str(exc)) from exc
    if isinstance(outcome, suite.SuiteResult):
        emit_json(_result_document(outcome))
        return suite.result_exit_code(outcome)
    emit_json(
        {
            "state": "skipped" if outcome.skipped else "started",
            "session_name": outcome.session_name,
            "worktree": str(outcome.worktree),
            "phase": outcome.phase_slug,
            "phase_head": outcome.phase_head,
            "log_path": str(outcome.log_path),
            "exit_path": str(outcome.exit_path),
            "run_id": outcome.run_id,
            "skip_reason": outcome.skip_reason,
            "policy": _policy_document(outcome.policy) if outcome.policy else None,
        }
    )
    return suite.SKIPPED_EXIT_CODE if outcome.skipped else 0


def _poll(args: argparse.Namespace) -> int:
    try:
        job = _job(args)
        result = suite.poll_suite(job, allow_dirty=args.allow_dirty)
    except _FAILURES as exc:
        raise CommandError(str(exc)) from exc
    if result is None:
        emit_json(
            {
                "state": "running",
                "session_name": job.session_name,
                "phase": job.phase_slug,
                "phase_head": job.phase_head,
                "log_path": str(job.log_path),
                "exit_path": str(job.exit_path),
                "run_id": job.run_id,
            }
        )
        return 3
    emit_json(_result_document(result))
    return suite.result_exit_code(result)


def _collect(args: argparse.Namespace) -> int:
    try:
        result = suite.collect_suite(_job(args), allow_dirty=args.allow_dirty)
    except _FAILURES as exc:
        raise CommandError(str(exc)) from exc
    emit_json(_result_document(result))
    return suite.result_exit_code(result)


def _record(args: argparse.Namespace) -> int:
    work = work_dir(args)
    try:
        job = _job(args)
        result = suite.poll_suite(job, allow_dirty=args.allow_dirty)
        if result is None:
            return fail(args, "suite is still running; poll it until it finishes", 3)
        if result.skipped:
            print(result.skip_reason, file=sys.stderr)
            return suite.SKIPPED_EXIT_CODE
        record = suite.record_suite_check_run(
            project=open_project(args, work, Access.WRITE),
            phase_slug=args.phase,
            effort=args.effort,
            suite=result,
            criterion_id=args.criterion_id,
        )
    except _FAILURES as exc:
        raise CommandError(str(exc)) from exc
    emit_json({"ok": True, "op": "suite-record", "record": record})
    return 0


def _cancel(args: argparse.Namespace) -> int:
    try:
        job = _job(args)
        state = suite.cancel_suite_run(job)
    except _FAILURES as exc:
        raise CommandError(str(exc)) from exc
    emit_json(
        {
            "ok": True,
            "op": "suite-cancel",
            "state": state,
            "session_name": job.session_name,
            "run_id": job.run_id,
        }
    )
    return 0 if state in ("requested", "cancelled", "completed", "skipped") else 2


def _add_job_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_run_id: bool = False,
) -> None:
    parser.add_argument("--phase", required=True, help="Phase slug")
    parser.add_argument(
        "--cwd",
        default=None,
        help="Phase worktree (default: process cwd)",
    )
    parser.add_argument(
        "--phase-head",
        default=None,
        help="Phase head revision (default: git HEAD in --cwd)",
    )
    parser.add_argument(
        "--session",
        default=None,
        help="Suite job label (default: orchestra-suite-<phase>)",
    )
    if include_run_id:
        parser.add_argument(
            "--run-id",
            default=None,
            help="Select this immutable run instead of the current run",
        )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow recording a pass on a dirty tree (revision=dirty + diff_sha256)",
    )


def _configure_policy(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cwd", default=None, help="Worktree (default: cwd)")


def _configure_start(parser: argparse.ArgumentParser) -> None:
    _add_job_arguments(parser)
    parser.add_argument(
        "--command",
        dest="suite_command",
        default=None,
        help="Override the configured suite command",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Stop the suite command after this many seconds",
    )


def _configure_run_job(parser: argparse.ArgumentParser) -> None:
    _add_job_arguments(parser, include_run_id=True)


def _configure_record(parser: argparse.ArgumentParser) -> None:
    _add_job_arguments(parser, include_run_id=True)
    parser.add_argument(
        "--effort",
        required=True,
        help="Effort/focus the check-run belongs to",
    )
    parser.add_argument(
        "--criterion-id",
        default=None,
        help="Criterion id (default: <phase>-suite)",
    )
    parser.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help=(
            "Store repo root (default: $ORCHESTRA_STORE, then resolve from --cwd). "
            "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
        ),
    )


def _configure_cancel(parser: argparse.ArgumentParser) -> None:
    _add_job_arguments(parser)
    parser.add_argument(
        "--run-id",
        required=True,
        help="Immutable run id returned by suite start",
    )


def commands() -> list[Command]:
    return [
        Command(
            "suite",
            "Phase suite: policy, start, poll, collect, cancel, record",
            children=(
                Command(
                    "policy",
                    "Print the configured orchestra.toml suite policy as JSON",
                    configure=_configure_policy,
                    handle=_policy,
                ),
                Command(
                    "start",
                    "Start the configured suite in a detached worker process",
                    configure=_configure_start,
                    handle=_start,
                ),
                Command(
                    "poll",
                    "Return the suite result when the background job finished, else 'running'",
                    configure=_configure_run_job,
                    handle=_poll,
                ),
                Command(
                    "collect",
                    "Collect the finished suite result (exit code, log, failing node ids)",
                    configure=_configure_run_job,
                    handle=_collect,
                ),
                Command(
                    "record",
                    "Collect a finished suite and write its tuner:check-run",
                    configure=_configure_record,
                    handle=_record,
                ),
                Command(
                    "cancel",
                    "Request cancellation of one selected suite run",
                    configure=_configure_cancel,
                    handle=_cancel,
                ),
            ),
        )
    ]
