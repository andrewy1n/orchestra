"""Subcommand dispatcher for the orchestra CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from orchestra.check import DEFAULT_TIMEOUT_S, run_check
from orchestra.close_batch import main as close_batch_main


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestra",
        description="orchestra CLI (plugin-local; shells to adaptive-artifacts).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser(
        "check",
        help="Run an acceptance verify_command and write a project:check-run",
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

    close_batch = sub.add_parser(
        "close-batch",
        help="Build NDJSON apply batch that closes a work-item",
    )
    close_batch.add_argument(
        "--input",
        default="-",
        help="close-request JSON path, or '-' for stdin (default)",
    )
    close_batch.add_argument(
        "--out",
        default="-",
        help="NDJSON output path, or '-' for stdout (default)",
    )
    close_batch.add_argument(
        "--cwd",
        default=None,
        help="git cwd for red-first ancestry checks (default: process cwd)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        work = Path(args.cwd) if args.cwd else Path.cwd()
        outcome = run_check(
            acceptance_id=args.acceptance,
            cwd=work,
            allow_dirty=args.allow_dirty,
            execution_report=args.execution_report,
            timeout=args.timeout,
        )
        if outcome.record is not None:
            print(json.dumps({"ok": True, "op": "check", "record": outcome.record}, indent=2))
        if outcome.message:
            print(outcome.message, file=sys.stderr)
        return outcome.exit_code
    if args.command == "close-batch":
        argv = ["--input", args.input, "--out", args.out]
        if args.cwd is not None:
            argv.extend(["--cwd", args.cwd])
        return close_batch_main(argv)
    parser.error(f"unknown command {args.command!r}")
    return 2
