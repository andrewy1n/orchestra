"""Handlers for `orchestra close` and `orchestra close-batch`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.types import JsonObject
from orchestra.canon.workspace import Access, StoreNotReady
from orchestra.conductor import close, close_batch
from orchestra.conductor.cli.workspace import (
    command_dir,
    not_ready_message,
    print_json,
    resolve_workspace,
)
from orchestra.conductor.github_pr import GitHubPRError, github_client
from orchestra.tools.errors import ToolError
from orchestra.tools.git import Git


def run_close(args: argparse.Namespace) -> int:
    if bool(args.phase) == bool(args.all):
        print("orchestra close: pass exactly one of --phase and --all", file=sys.stderr)
        return 2
    work = command_dir(args).resolve()
    try:
        project = resolve_workspace(args.store, work, Access.WRITE).open()
        repo = Git(work).primary_checkout()
        states = github_client(repo)
        if args.all:
            outcomes = close.close_all(project, repo, states, work)
        else:
            outcomes = (close.close_phase(project, repo, args.phase, states, work),)
    except StoreNotReady as exc:
        print(f"orchestra close: {not_ready_message(exc, work)}", file=sys.stderr)
        return 2
    except (
        close.CloseError,
        GitHubPRError,
        LookupError,
        OSError,
        RuntimeError,
        StoreBindingError,
        StoreError,
        ToolError,
        ValueError,
    ) as exc:
        print(f"orchestra close: {exc}", file=sys.stderr)
        return 2
    report = close.CloseReport.from_outcomes(outcomes, all_phases=args.all)
    if report.all_phases:
        print_json(
            {
                "ok": report.ok,
                "op": "close",
                "phases": [_result_json(item) for item in report.results],
                "errors": list(report.errors),
            }
        )
    else:
        print_json(_result_json(report.results[0]))
    for line in report.diagnostics:
        print(f"orchestra close: {line}", file=sys.stderr)
    return report.exit_code


def run_close_batch(args: argparse.Namespace) -> int:
    start = Path.cwd()
    argv = ["--input", args.input, "--out", args.out]
    if args.cwd is not None:
        argv.extend(["--cwd", args.cwd])
    try:
        return close_batch.main(
            argv, workspace=lambda: resolve_workspace(args.store, start, Access.READ)
        )
    except StoreNotReady as exc:
        print(f"close refused: {not_ready_message(exc, start)}", file=sys.stderr)
        return 2


def _result_json(result: close.CloseResult) -> JsonObject:
    return {
        "ok": not result.refusals,
        "op": "close",
        "phase": result.phase,
        "pull_request": {
            "number": result.number,
            "url": result.url,
            "state": result.state,
            "head_sha": result.head_sha,
        },
        "ready": result.ready,
        "refusals": list(result.refusals),
        "actions": list(result.actions),
        "message": result.message,
    }
