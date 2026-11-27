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
from orchestra.tools import command_kit
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
    command_kit.mount(sub, views_cli.commands())
    command_kit.mount(sub, stage_cli.commands())
    command_kit.mount(sub, views_status.commands())
    command_kit.mount(sub, metrics_cli.commands())
    command_kit.mount(sub, tuner_cli.commands())
    command_kit.mount(sub, sessions_cli.commands())
    command_kit.mount(
        sub,
        conductor_cli.commands(
            render_brief=views_cli.render_brief,
            architecture=conductor_cli.ArchitectureChanges(
                review=views_cli.architecture_proposal.architecture_review,
                proposed_constraint=composer_cli.architecture_change.proposed_constraint,
                reconcile=composer_cli.architecture_change.reconcile_architecture,
            ),
        ),
    )
    command_kit.mount(sub, score_cli.commands())
    command_kit.mount(sub, canon_cli.commands(scan=scan, recover=recover))
    command_kit.mount(sub, composer_cli.commands())
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = _build_parser()
    args, extra = parser.parse_known_args(argv)
    if extra and not getattr(args, "passthrough", False):
        parser.error(f"unrecognized arguments: {' '.join(extra)}")
    return command_kit.run(args, extra)


if __name__ == "__main__":
    sys.exit(main())
