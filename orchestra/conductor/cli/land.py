"""Handler for `orchestra land`."""

from __future__ import annotations

import argparse
import sys

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.workspace import Access, StoreNotReady
from orchestra.conductor import land
from orchestra.conductor.cli.workspace import (
    command_dir,
    not_ready_message,
    print_json,
    resolve_workspace,
)
from orchestra.conductor.github_pr import GitHubPRError, github_client

GATE_FAILED_EXIT = 5


def run_land(args: argparse.Namespace) -> int:
    work = command_dir(args).resolve()
    try:
        client = github_client(work, args.remote)
        workspace = resolve_workspace(args.store, work, Access.WRITE)
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
        print(f"orchestra land: {not_ready_message(exc, work)}", file=sys.stderr)
        return 2
    except land.LandGateError as exc:
        for line in exc.lines:
            print(f"orchestra land: {args.phase}: {line}", file=sys.stderr)
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
        print(f"orchestra land: {exc}", file=sys.stderr)
        return 2
    print_json(
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
