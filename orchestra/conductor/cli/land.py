"""Handler for `orchestra land`."""

from __future__ import annotations

import argparse

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.workspace import Access, StoreNotReady, Workspace, not_ready_message
from orchestra.conductor import land
from orchestra.conductor.cli.options import store_path, work_dir
from orchestra.conductor.github_pr import GitHubPRError, github_client
from orchestra.tools.command_kit import Command, CommandError, emit_json, fail

GATE_FAILED_EXIT = 5


def _configure(parser: argparse.ArgumentParser) -> None:
    parser.description = (
        "Run the phase gate and publish the pull request. The GitHub landing adapter "
        "waits for CI when no merge evidence adapter is configured."
    )
    parser.add_argument("--phase", required=True, help="Phase slug")
    parser.add_argument("--cwd", default=None, help="Phase worktree (default: process cwd)")
    parser.add_argument("--base", default="main", help="Pull request base branch")
    parser.add_argument("--remote", default="origin", help="Git remote to publish")
    parser.add_argument(
        "--poll-interval", type=float, default=10, help="CI polling interval in seconds"
    )
    parser.add_argument("--timeout", type=float, default=1800, help="Maximum CI wait in seconds")
    parser.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help=(
            "Store repo root (default: $ORCHESTRA_STORE, then resolve from --cwd). "
            "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
        ),
    )


def _handle(args: argparse.Namespace) -> int:
    work = work_dir(args).resolve()
    try:
        client = github_client(work, args.remote)
        workspace = Workspace.resolve(work, store_path(args), Access.WRITE)
        result = land.land_phase(
            workspace,
            args.phase,
            work,
            client,
            base=args.base,
            remote=args.remote,
            poll_interval_s=args.poll_interval,
            timeout_s=args.timeout,
        )
    except StoreNotReady as exc:
        raise CommandError(not_ready_message(exc, work)) from exc
    except land.LandGateError as exc:
        for line in exc.lines:
            fail(args, f"{args.phase}: {line}")
        return GATE_FAILED_EXIT
    except (
        GitHubPRError,
        LookupError,
        OSError,
        RuntimeError,
        StoreBindingError,
        StoreError,
        TimeoutError,
        ValueError,
    ) as exc:
        raise CommandError(str(exc)) from exc
    emit_json(
        {
            "ok": result.succeeded,
            "op": "land",
            "pull_request": {
                "number": result.number,
                "url": result.url,
                "head_sha": result.head_sha,
            },
            "checks": [
                {"name": check.name, "status": check.status, "conclusion": check.conclusion}
                for check in result.checks
            ],
            "statuses": result.statuses,
            "result": result.result,
        }
    )
    return result.exit_code


def commands() -> list[Command]:
    return [
        Command(
            "land",
            "Run the phase gate and publish the pull request",
            configure=_configure,
            handle=_handle,
        )
    ]
