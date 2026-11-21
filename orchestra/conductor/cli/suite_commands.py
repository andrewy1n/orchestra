"""Handlers for `orchestra suite`."""

from __future__ import annotations

import argparse
import sys

from orchestra.canon.project import StoreBindingError
from orchestra.canon.workspace import Access, StoreNotReady
from orchestra.conductor import suite
from orchestra.conductor.cli.workspace import (
    command_dir,
    not_ready_message,
    print_json,
    resolve_workspace,
)

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
        worktree=command_dir(args),
        phase_slug=args.phase,
        session_name=args.session,
        run_id=getattr(args, "run_id", None),
    )


def _policy(args: argparse.Namespace) -> int:
    try:
        policy = suite.load_suite_policy(command_dir(args))
    except _FAILURES as exc:
        print(f"orchestra suite policy: {exc}", file=sys.stderr)
        return 2
    print_json(_policy_document(policy))
    return 0


def _start(args: argparse.Namespace) -> int:
    try:
        outcome = suite.start_suite_background(
            worktree=command_dir(args),
            phase_slug=args.phase,
            phase_head=args.phase_head,
            session_name=args.session,
            suite_command=args.suite_command,
            allow_dirty=args.allow_dirty,
            timeout=args.timeout,
        )
    except _FAILURES as exc:
        print(f"orchestra suite start: {exc}", file=sys.stderr)
        return 2
    if isinstance(outcome, suite.SuiteResult):
        print_json(_result_document(outcome))
        return suite.result_exit_code(outcome)
    print_json(
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
        print(f"orchestra suite poll: {exc}", file=sys.stderr)
        return 2
    if result is None:
        print_json(
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
    print_json(_result_document(result))
    return suite.result_exit_code(result)


def _collect(args: argparse.Namespace) -> int:
    try:
        result = suite.collect_suite(_job(args), allow_dirty=args.allow_dirty)
    except _FAILURES as exc:
        print(f"orchestra suite collect: {exc}", file=sys.stderr)
        return 2
    print_json(_result_document(result))
    return suite.result_exit_code(result)


def _record(args: argparse.Namespace) -> int:
    work = command_dir(args)
    try:
        job = _job(args)
        result = suite.poll_suite(job, allow_dirty=args.allow_dirty)
        if result is None:
            print(
                "orchestra suite record: suite is still running; poll it until it finishes",
                file=sys.stderr,
            )
            return 3
        if result.skipped:
            print(result.skip_reason, file=sys.stderr)
            return suite.SKIPPED_EXIT_CODE
        workspace = resolve_workspace(args.store, work, Access.WRITE)
        record = suite.record_suite_check_run(
            store_root=workspace.root,
            store_dir=workspace.store,
            phase_slug=args.phase,
            effort=args.effort,
            suite=result,
            criterion_id=args.criterion_id,
        )
    except StoreNotReady as exc:
        print(f"orchestra suite record: {not_ready_message(exc, work)}", file=sys.stderr)
        return 2
    except _FAILURES as exc:
        print(f"orchestra suite record: {exc}", file=sys.stderr)
        return 2
    print_json({"ok": True, "op": "suite-record", "record": record})
    return 0


def _cancel(args: argparse.Namespace) -> int:
    try:
        job = _job(args)
        state = suite.cancel_suite_run(job)
    except _FAILURES as exc:
        print(f"orchestra suite cancel: {exc}", file=sys.stderr)
        return 2
    print_json(
        {
            "ok": True,
            "op": "suite-cancel",
            "state": state,
            "session_name": job.session_name,
            "run_id": job.run_id,
        }
    )
    return 0 if state in ("requested", "cancelled", "completed", "skipped") else 2


_ACTIONS = {
    "policy": _policy,
    "start": _start,
    "poll": _poll,
    "collect": _collect,
    "cancel": _cancel,
    "record": _record,
}


def run_suite(args: argparse.Namespace) -> int:
    return _ACTIONS[args.action](args)
