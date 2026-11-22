"""CLI wiring for `orchestra sessions`."""

from __future__ import annotations

import argparse

from orchestra.sessions import aggregate, report
from orchestra.tools.command_kit import Command, CommandError


def _configure_report(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "root",
        nargs="?",
        default=None,
        help="Transcript root (default: ~/.claude/projects)",
    )
    parser.add_argument(
        "--records",
        action="store_true",
        help="Attach matched record counts to each session",
    )


def _configure_aggregate(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "report",
        nargs="?",
        default="-",
        help="report JSONL path, or '-' for stdin (default)",
    )


def _report(args: argparse.Namespace) -> int:
    try:
        return report(args.root, records=args.records)
    except OSError as exc:
        raise CommandError(str(exc)) from exc


def _aggregate(args: argparse.Namespace) -> int:
    try:
        return aggregate(args.report)
    except OSError as exc:
        raise CommandError(str(exc)) from exc


def commands() -> list[Command]:
    return [
        Command(
            "sessions",
            "Summarize Claude Code session transcripts",
            children=(
                Command(
                    "report",
                    "Print one JSON summary per session transcript",
                    configure=_configure_report,
                    handle=_report,
                ),
                Command(
                    "aggregate",
                    "Print one aggregate document for a report JSONL file",
                    configure=_configure_aggregate,
                    handle=_aggregate,
                ),
            ),
        )
    ]
