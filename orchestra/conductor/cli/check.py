"""Parser and handler for `orchestra check`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Protocol

from orchestra.canon.workspace import Access, StoreNotReady
from orchestra.conductor.check import DEFAULT_TIMEOUT_S, run_check
from orchestra.conductor.cli.workspace import not_ready_message, resolve_workspace

STORE_NOT_READY_EXIT = 4


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


def add_check_parser(sub: SubparserGroup) -> None:
    check = sub.add_parser(
        "check",
        help="Run an acceptance verify_command and write an tuner:check-run",
    )
    check.add_argument("--acceptance", required=True, help="Acceptance record id")
    check.add_argument(
        "--cwd",
        default=None,
        help="Directory for git revision and verify_command (default: process cwd)",
    )
    check.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow recording a pass on a dirty tree (revision=dirty + diff_sha256)",
    )
    check.add_argument(
        "--execution-report",
        default=None,
        help="Optional execution-report id to link via informed_by",
    )
    check.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_S,
        help=f"verify_command timeout in seconds (default: {DEFAULT_TIMEOUT_S:g})",
    )
    check.add_argument(
        "--store",
        default=None,
        metavar="DIR",
        help=(
            "Store repo root (default: $ORCHESTRA_STORE, then resolve from the process cwd). "
            "An explicit --store or $ORCHESTRA_STORE beats $CANON_STORE"
        ),
    )


def run_check_command(args: argparse.Namespace) -> int:
    work = Path(args.cwd) if args.cwd else Path.cwd()
    try:
        workspace = resolve_workspace(args.store, Path.cwd(), Access.WRITE)
    except StoreNotReady as exc:
        print(f"orchestra check: {not_ready_message(exc, Path.cwd())}", file=sys.stderr)
        return STORE_NOT_READY_EXIT
    try:
        project = workspace.open()
    except StoreNotReady as exc:
        print(f"orchestra check: {not_ready_message(exc, Path.cwd())}", file=sys.stderr)
        return STORE_NOT_READY_EXIT
    outcome = run_check(
        acceptance_id=args.acceptance,
        cwd=work,
        project=project,
        allow_dirty=args.allow_dirty,
        execution_report=args.execution_report,
        timeout=args.timeout,
    )
    if outcome.record is not None:
        print(
            json.dumps(
                {
                    "ok": True,
                    "op": "check",
                    "record": outcome.record,
                    "reused": outcome.reused,
                },
                indent=2,
            )
        )
    if outcome.message:
        print(outcome.message, file=sys.stderr)
    return outcome.exit_code
