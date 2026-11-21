"""CLI wiring for `orchestra sessions`."""

from __future__ import annotations

import argparse
import sys
from typing import Protocol

from orchestra.sessions import aggregate, report

COMMANDS = frozenset({"sessions"})


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


def add_parsers(sub: SubparserGroup) -> None:
    sessions = sub.add_parser("sessions", help="Summarize Claude Code session transcripts")
    sessions_sub = sessions.add_subparsers(dest="action", required=True)
    report_parser = sessions_sub.add_parser(
        "report", help="Print one JSON summary per session transcript"
    )
    report_parser.add_argument(
        "root",
        nargs="?",
        default=None,
        help="Transcript root (default: ~/.claude/projects)",
    )
    report_parser.add_argument(
        "--records",
        action="store_true",
        help="Attach matched record counts to each session",
    )
    aggregate_parser = sessions_sub.add_parser(
        "aggregate", help="Print one aggregate document for a report JSONL file"
    )
    aggregate_parser.add_argument(
        "report",
        nargs="?",
        default="-",
        help="report JSONL path, or '-' for stdin (default)",
    )


def run(args: argparse.Namespace) -> int:
    try:
        if args.action == "report":
            return report(args.root, records=args.records)
        return aggregate(args.report)
    except OSError as exc:
        print(f"orchestra sessions: {exc}", file=sys.stderr)
        return 2
