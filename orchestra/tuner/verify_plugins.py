"""CLI for running and signing configured built-in verification plugins."""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

from orchestra.tools import command_kit
from orchestra.tools.command_kit import Command, CommandError
from orchestra.tuner.plugins.api import PluginContext
from orchestra.tuner.plugins.manifest import ManifestError
from orchestra.tuner.plugins.plugin_evidence import dispatch_signed_plugins


def _configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cwd", default=None, help="Repository root (default: process cwd)")
    parser.add_argument("--stage", choices=("task", "phase", "milestone"), required=True)
    parser.add_argument("--revision", default="HEAD", help="Target commit (default: HEAD)")
    parser.add_argument("--test", action="append", default=[], dest="tests", metavar="NODE")
    parser.add_argument(
        "--review-output",
        default=None,
        help="Structured reviewer output path, or - to read it from stdin",
    )
    parser.add_argument("--key", required=True, help="SSH private key path for signing")


def _handle(args: argparse.Namespace) -> int:
    work = Path(args.cwd) if args.cwd else Path.cwd()
    try:
        reviewer_output = None
        if args.review_output == "-":
            reviewer_output = sys.stdin.read()
        elif args.review_output is not None:
            reviewer_output = Path(args.review_output).read_text(encoding="utf-8")
        evidence = dispatch_signed_plugins(
            PluginContext(
                root=work,
                stage=args.stage,
                revision=args.revision,
                tests=tuple(args.tests),
                reviewer_output=reviewer_output,
            ),
            key_path=args.key,
        )
    except (OSError, ValueError, ManifestError) as exc:
        raise CommandError(str(exc), 2) from exc
    command_kit.emit_json([asdict(item) for item in evidence], compact=True)
    return 0 if all(item.result == "pass" for item in evidence) else 1


def command() -> Command:
    return Command(
        "plugins",
        "Run configured built-in plugins and emit signed evidence",
        configure=_configure,
        handle=_handle,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orchestra verify plugins",
        description="Run configured built-in plugins and emit signed evidence.",
    )
    _configure(parser)
    args = parser.parse_args(argv)
    args.handler = _handle
    args.command_path = ("verify", "plugins")
    return command_kit.run(args)
