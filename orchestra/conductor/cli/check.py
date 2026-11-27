"""Parser and handler for `orchestra check`."""

from __future__ import annotations

import argparse
import sys
from functools import partial
from pathlib import Path

from orchestra.canon.workspace import Access
from orchestra.conductor.cli.options import open_project
from orchestra.conductor.verification.check import (
    DEFAULT_TIMEOUT_S,
    ProposedConstraintReader,
    run_check,
    run_proposed_constraint_check,
    run_standing_constraint_check,
)
from orchestra.tools.command_kit import Command, emit_json


def _configure(check: argparse.ArgumentParser) -> None:
    target = check.add_mutually_exclusive_group(required=True)
    target.add_argument("--acceptance", help="Acceptance record id")
    target.add_argument(
        "--standing-constraint",
        metavar="NAME",
        help="Subject of a standing constraint pinned by --phase",
    )
    target.add_argument(
        "--proposed-constraint",
        metavar="ID",
        help="Pinned constraint-change record id to check at the candidate commit",
    )
    check.add_argument(
        "--phase", default=None, help="Phase whose design or proposal pins the constraint"
    )
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


def _handle(args: argparse.Namespace, reader: ProposedConstraintReader | None) -> int:
    work = Path(args.cwd) if args.cwd else Path.cwd()
    project = open_project(args, Path.cwd(), Access.WRITE, refused_exit=4)
    if args.proposed_constraint:
        if not args.phase or reader is None or args.allow_dirty:
            print("--proposed-constraint requires --phase and a clean candidate", file=sys.stderr)
            return 4
        outcome = run_proposed_constraint_check(
            change_id=args.proposed_constraint,
            phase=args.phase,
            cwd=work,
            project=project,
            reader=reader,
            timeout=args.timeout,
        )
    elif args.standing_constraint:
        if not args.phase:
            print("--standing-constraint requires --phase", file=sys.stderr)
            return 4
        outcome = run_standing_constraint_check(
            name=args.standing_constraint,
            phase=args.phase,
            cwd=work,
            project=project,
            allow_dirty=args.allow_dirty,
            timeout=args.timeout,
        )
    else:
        outcome = run_check(
            acceptance_id=args.acceptance,
            cwd=work,
            project=project,
            allow_dirty=args.allow_dirty,
            execution_report=args.execution_report,
            timeout=args.timeout,
        )
    if outcome.record is not None:
        emit_json(
            {
                "ok": True,
                "op": "check",
                "record": outcome.record,
                "reused": outcome.reused,
            }
        )
    if outcome.message:
        print(outcome.message, file=sys.stderr)
    return outcome.exit_code


def commands(reader: ProposedConstraintReader | None = None) -> list[Command]:
    return [
        Command(
            "check",
            "Run an acceptance verify_command or standing constraint check and write an tuner:check-run",
            configure=_configure,
            handle=partial(_handle, reader=reader),
        )
    ]
