"""Handlers for `orchestra close` and `orchestra close-batch`."""

from __future__ import annotations

import argparse
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.types import JsonObject
from orchestra.canon.workspace import Access, resolve_for_command
from orchestra.conductor import close
from orchestra.conductor.cli.options import open_project, store_path, work_dir
from orchestra.conductor.landing.github_pr import GitHubPRError, github_client
from orchestra.conductor.tasks.close import close_batch
from orchestra.tools.command_kit import Command, CommandError, emit_json, fail
from orchestra.tools.errors import ToolError
from orchestra.tools.git import Git


def _configure_close(parser: argparse.ArgumentParser) -> None:
    parser.description = (
        "After the pull request merges, close removes the worktrees and branches of the "
        "phase and closes the phase. Run it from the main checkout."
    )
    parser.add_argument("--phase", default=None, help="Phase slug")
    parser.add_argument(
        "--all", action="store_true", help="Close every landed phase that still has work to close"
    )
    parser.add_argument("--cwd", default=None, help="Directory inside the repo (default: cwd)")
    parser.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help=(
            "Store repo root (default: $ORCHESTRA_STORE, then resolve from --cwd). "
            "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
        ),
    )


def _configure_close_batch(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--input",
        default="-",
        help="close-request JSON path, or '-' for stdin (default)",
    )
    parser.add_argument(
        "--out",
        default="-",
        help="NDJSON output path, or '-' for stdout (default)",
    )
    parser.add_argument(
        "--cwd",
        default=None,
        help="git cwd for red-first ancestry checks (default: process cwd)",
    )
    parser.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help="Store repo root (default: $ORCHESTRA_STORE, then resolve from the process cwd)",
    )


def _close(args: argparse.Namespace) -> int:
    if bool(args.phase) == bool(args.all):
        raise CommandError("pass exactly one of --phase and --all")
    work = work_dir(args).resolve()
    project = open_project(args, work, Access.WRITE)
    try:
        repo = Git(work).primary_checkout()
        states = github_client(repo)
        if args.all:
            outcomes = close.close_all(project, repo, states, work)
        else:
            outcomes = (close.close_phase(project, repo, args.phase, states, work),)
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
        raise CommandError(str(exc)) from exc
    report = close.CloseReport.from_outcomes(outcomes, all_phases=args.all)
    if report.all_phases:
        emit_json(
            {
                "ok": report.ok,
                "op": "close",
                "phases": [_result_json(item) for item in report.results],
                "errors": list(report.errors),
            }
        )
    else:
        emit_json(_result_json(report.results[0]))
    for line in report.diagnostics:
        fail(args, line)
    return report.exit_code


def _close_batch(args: argparse.Namespace) -> int:
    start = Path.cwd()
    argv = ["--input", args.input, "--out", args.out]
    if args.cwd is not None:
        argv.extend(["--cwd", args.cwd])
    return close_batch.main(
        argv, workspace=lambda: resolve_for_command(start, Access.READ, store=store_path(args))
    )


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


def commands() -> list[Command]:
    return [
        Command(
            "close-batch",
            "Build NDJSON apply batch that closes a work-item",
            configure=_configure_close_batch,
            handle=_close_batch,
        ),
        Command(
            "close",
            "After the pull request merges, remove the phase worktrees and branches "
            "and close the phase",
            configure=_configure_close,
            handle=_close,
        ),
    ]
