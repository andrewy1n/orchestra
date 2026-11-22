"""Subcommand dispatcher for the orchestra CLI."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from types import ModuleType

from orchestra.canon import cli as canon_cli
from orchestra.composer import cli as composer_cli
from orchestra.conductor import cli as conductor_cli
from orchestra.metrics import cli as metrics_cli
from orchestra.score import cli as score_cli
from orchestra.sessions import cli as sessions_cli
from orchestra.stage import cli as stage_cli
from orchestra.tools import command_kit
from orchestra.tools.command_kit import Command
from orchestra.tuner import cli as tuner_cli
from orchestra.views import cli as views_cli
from orchestra.views import status as views_status


def _mount(sub: command_kit.SubparserGroup, module: ModuleType, legacy: Callable[[], None]) -> None:
    commands: Callable[[], Sequence[Command]] | None = getattr(module, "commands", None)
    if commands is None:
        legacy()
    else:
        command_kit.mount(sub, commands())


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
    command_kit.mount(sub, conductor_cli.commands(render_brief=views_cli.render_brief))
    command_kit.mount(sub, score_cli.commands())
    _mount(sub, canon_cli, lambda: canon_cli.add_parsers(sub, scan=scan, recover=recover))
    command_kit.mount(sub, composer_cli.commands())
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = _build_parser()
    args, extra = parser.parse_known_args(argv)
    bound = getattr(args, "handler", None) is not None
    if extra and not (bound and getattr(args, "passthrough", False)):
        parser.error(f"unrecognized arguments: {' '.join(extra)}")
    if bound:
        return command_kit.run(args, extra)
    if args.command in canon_cli.COMMANDS:
        return canon_cli.run(args)
    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
