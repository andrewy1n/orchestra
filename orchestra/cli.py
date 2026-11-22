"""Subcommand dispatcher for the orchestra CLI."""

from __future__ import annotations

import argparse
import sys

from orchestra.canon import cli as canon_cli
from orchestra.composer import cli as composer_cli
from orchestra.conductor import cli as conductor_cli
from orchestra.metrics import cli as metrics_cli
from orchestra.score import cli as score_cli
from orchestra.sessions import cli as sessions_cli
from orchestra.stage import cli as stage_cli
from orchestra.tuner import cli as tuner_cli
from orchestra.views import cli as views_cli
from orchestra.views import status as views_status


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestra",
        description=(
            "orchestra CLI: checks, reviewer briefs, phase suite, "
            "and store access through the artifact library."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    scan, recover = stage_cli.store_operations()
    views_cli.add_parsers(sub)
    stage_cli.add_parsers(sub)
    views_status.add_parser(sub)
    metrics_cli.add_parsers(sub)
    tuner_cli.add_parsers(sub)
    sessions_cli.add_parsers(sub)
    conductor_cli.add_parsers(sub, render_brief=views_cli.render_brief)
    score_cli.add_parsers(sub)
    canon_cli.add_parsers(sub, scan=scan, recover=recover)
    composer_cli.add_parsers(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = _build_parser()
    args, extra = parser.parse_known_args(argv)
    if extra and args.command != tuner_cli.PASSTHROUGH:
        parser.error(f"unrecognized arguments: {' '.join(extra)}")
    if args.command in tuner_cli.COMMANDS:
        return tuner_cli.run(args, extra)
    if args.command in sessions_cli.COMMANDS:
        return sessions_cli.run(args)
    if args.command in conductor_cli.COMMANDS:
        return conductor_cli.run(args)
    if args.command in score_cli.COMMANDS:
        return score_cli.run(args)
    if args.command in canon_cli.COMMANDS:
        return canon_cli.run(args)
    if args.command in composer_cli.COMMANDS:
        return composer_cli.run(args)
    if args.command == "status":
        return views_status.run(args)
    if args.command in metrics_cli.COMMANDS:
        return metrics_cli.run(args)
    if args.command in stage_cli.COMMANDS:
        return stage_cli.run(args)
    if args.command in views_cli.COMMANDS:
        return views_cli.run(args)
    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
