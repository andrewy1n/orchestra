"""CLI wiring for `orchestra idea` and `orchestra place`."""

from __future__ import annotations

import argparse
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.workspace import Access, open_for_command
from orchestra.composer.architecture_reconciliation import (
    reconcile_architecture as reconcile_architecture,
)
from orchestra.composer.idea import IdeaError, capture
from orchestra.composer.placement import PlacementError, place
from orchestra.tools.command_kit import Command, CommandError


def _configure_idea(idea: argparse.ArgumentParser) -> None:
    idea.add_argument("title", help="Idea title; subject is the slugified title")
    idea.add_argument("--area", default=None, help="composer:area subject slug")
    idea.add_argument("--effort", default=None, help="score:effort subject slug")
    idea.add_argument("--source", default=None, help="Idea source text")
    idea.add_argument(
        "--body-file",
        default=None,
        help="Append this file's text to the idea body below the title",
    )


def _configure_place(place_parser: argparse.ArgumentParser) -> None:
    place_parser.add_argument("effort", help="score:effort subject slug")
    place_parser.add_argument("area", help="composer:area subject slug")


def _idea(args: argparse.Namespace) -> int:
    extra_body = None
    if args.body_file is not None:
        try:
            extra_body = Path(args.body_file).read_text(encoding="utf-8")
        except OSError as exc:
            raise CommandError(str(exc), 1) from exc
    project = open_for_command(Path.cwd(), Access.WRITE)
    try:
        record = capture(
            project,
            args.title,
            area=args.area,
            effort=args.effort,
            source=args.source,
            body=extra_body,
        )
    except (IdeaError, StoreBindingError, StoreError) as exc:
        raise CommandError(str(exc), 1) from exc
    print(record["subject"])
    return 0


def _place(args: argparse.Namespace) -> int:
    project = open_for_command(Path.cwd(), Access.WRITE)
    try:
        record = place(project, args.effort, args.area)
    except (PlacementError, StoreBindingError, StoreError) as exc:
        raise CommandError(str(exc), 1) from exc
    print(record["subject"])
    return 0


def commands() -> list[Command]:
    return [
        Command(
            "idea",
            "Capture an open composer idea from a title",
            configure=_configure_idea,
            handle=_idea,
        ),
        Command(
            "place",
            "Place an effort in a composer area",
            configure=_configure_place,
            handle=_place,
        ),
    ]
