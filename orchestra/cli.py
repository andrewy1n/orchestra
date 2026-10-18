"""Subcommand dispatcher for the orchestra CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from orchestra.check import DEFAULT_TIMEOUT_S, run_check
from orchestra.close_batch import main as close_batch_main
from orchestra.contract import contract_path
from orchestra.project_field import STOPPED, rewrite_project_field
from orchestra.sessions import aggregate as aggregate_sessions
from orchestra.sessions import report as report_sessions


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

    install = sub.add_parser(
        "install",
        help="Install orchestra payload for one or more agent hosts",
    )
    install.add_argument(
        "--only",
        action="append",
        metavar="HOST",
        default=[],
        help="Install only this provider id; repeat for more (default: all)",
    )
    install.add_argument(
        "--all",
        action="store_true",
        help="Select every provider in the matrix",
    )
    install.add_argument(
        "--global",
        dest="global_",
        action="store_true",
        help="Install into user directories instead of the project",
    )
    install.add_argument(
        "--copy",
        action="store_true",
        help="Copy payload instead of symlinking to this checkout",
    )
    install.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and write nothing",
    )
    install.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove exactly what the adapter registered",
    )
    install.add_argument(
        "--home",
        default=None,
        metavar="DIR",
        help="Redirect the whole install under DIR (tests, throwaway homes)",
    )

    contract = sub.add_parser(
        "contract",
        help="Print the bundled project-design contract",
    )
    contract.add_argument(
        "--path",
        action="store_true",
        help="Print the contract file path instead of its contents",
    )
    contract.add_argument(
        "--write",
        metavar="PATH",
        default=None,
        help="Write the bundled contract to PATH",
    )

    project_field = sub.add_parser(
        "project-field",
        help="Align a design file's project field with orchestra",
    )
    project_field_sub = project_field.add_subparsers(dest="action", required=True)
    rewrite = project_field_sub.add_parser(
        "rewrite",
        help="Rewrite the project field in place when it is affidavit",
    )
    rewrite.add_argument("design", help="Path to a project-design.json")
    rewrite.add_argument(
        "--json",
        action="store_true",
        help="Print the outcome as JSON instead of one word",
    )

    sessions = sub.add_parser(
        "sessions",
        help="Summarize Claude Code session transcripts",
    )
    sessions_sub = sessions.add_subparsers(dest="action", required=True)
    report = sessions_sub.add_parser(
        "report",
        help="Print one JSON summary per session transcript",
    )
    report.add_argument(
        "root",
        nargs="?",
        default=None,
        help="Transcript root (default: ~/.claude/projects)",
    )
    report.add_argument(
        "--records",
        action="store_true",
        help="Attach matched record counts to each session",
    )
    aggregate = sessions_sub.add_parser(
        "aggregate",
        help="Print one aggregate document for a report JSONL file",
    )
    aggregate.add_argument(
        "report",
        nargs="?",
        default="-",
        help="report JSONL path, or '-' for stdin (default)",
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
    if args.command == "install":
        from orchestra.install import main as install_main

        return install_main(args)
    if args.command == "contract":
        try:
            path = contract_path()
            text = path.read_text(encoding="utf-8")
            json.loads(text)
            if args.write is not None:
                destination = Path(args.write).expanduser()
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(text, encoding="utf-8")
                print(destination)
                return 0
        except (OSError, ValueError) as exc:
            print(f"orchestra contract: {exc}", file=sys.stderr)
            return 1
        if args.path:
            print(path)
            return 0
        print(text, end="" if text.endswith("\n") else "\n")
        return 0
    if args.command == "project-field":
        try:
            outcome = rewrite_project_field(args.design)
        except (OSError, ValueError) as exc:
            print(f"orchestra project-field: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps({"op": "project-field", "path": args.design, "outcome": outcome}))
        else:
            print(outcome)
        return 1 if outcome == STOPPED else 0
    if args.command == "sessions":
        try:
            if args.action == "report":
                return report_sessions(args.root, records=args.records)
            return aggregate_sessions(args.report)
        except (OSError, ModuleNotFoundError) as exc:
            print(f"orchestra sessions: {exc}", file=sys.stderr)
            return 2
    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
