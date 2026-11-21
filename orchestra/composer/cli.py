"""CLI wiring for `orchestra idea` and `orchestra place`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Protocol

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project, StoreBindingError
from orchestra.canon.workspace import Access, StoreNotReady, Workspace, not_ready_message
from orchestra.composer.idea import IdeaError, capture
from orchestra.composer.placement import PlacementError, place

COMMANDS = frozenset({"idea", "place"})


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


def add_parsers(sub: SubparserGroup) -> None:
    idea = sub.add_parser("idea", help="Capture an open composer idea from a title")
    idea.add_argument("title", help="Idea title; subject is the slugified title")
    idea.add_argument("--area", default=None, help="composer:area subject slug")
    idea.add_argument("--effort", default=None, help="score:effort subject slug")
    idea.add_argument("--source", default=None, help="Idea source text")
    idea.add_argument(
        "--body-file",
        default=None,
        help="Append this file's text to the idea body below the title",
    )

    place_parser = sub.add_parser("place", help="Place an effort in a composer area")
    place_parser.add_argument("effort", help="score:effort subject slug")
    place_parser.add_argument("area", help="composer:area subject slug")


def _open_project() -> Project:
    return Workspace.resolve(Path.cwd(), access=Access.WRITE).open()


def _cmd_idea(args: argparse.Namespace) -> int:
    extra_body = None
    if args.body_file is not None:
        try:
            extra_body = Path(args.body_file).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"orchestra idea: {exc}", file=sys.stderr)
            return 1
    try:
        record = capture(
            _open_project(),
            args.title,
            area=args.area,
            effort=args.effort,
            source=args.source,
            body=extra_body,
        )
    except StoreNotReady as exc:
        print(f"orchestra idea: {not_ready_message(exc, Path.cwd())}", file=sys.stderr)
        return 1
    except (IdeaError, StoreBindingError, StoreError) as exc:
        print(f"orchestra idea: {exc}", file=sys.stderr)
        return 1
    print(record["subject"])
    return 0


def _cmd_place(args: argparse.Namespace) -> int:
    try:
        record = place(_open_project(), args.effort, args.area)
    except StoreNotReady as exc:
        print(f"orchestra place: {not_ready_message(exc, Path.cwd())}", file=sys.stderr)
        return 1
    except (PlacementError, StoreBindingError, StoreError) as exc:
        print(f"orchestra place: {exc}", file=sys.stderr)
        return 1
    print(record["subject"])
    return 0


def run(args: argparse.Namespace) -> int:
    if args.command == "idea":
        return _cmd_idea(args)
    return _cmd_place(args)
