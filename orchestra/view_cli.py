"""CLI wiring for the view and session-hook commands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

COMMANDS = frozenset({"handoff", "view", "brief", "hook-start", "hook-stop"})


def add_parsers(sub) -> None:
    handoff = sub.add_parser("handoff", help="Print the handoff markdown")
    handoff.add_argument("--effort", default=None, help="Limit to one effort slug")
    view = sub.add_parser("view", help="Print a derived view as markdown")
    view.add_argument("name", choices=("plan", "status", "verification", "roadmap"))
    view.add_argument("--effort", default=None, help="Limit to one effort slug")
    brief = sub.add_parser("brief", help="Print one work-item's brief")
    brief.add_argument("subject", help="Work-item subject")
    for name, text in (
        ("hook-start", "SessionStart hook: inject the handoff"),
        ("hook-stop", "Stop hook: block on validation errors new this session"),
    ):
        hook = sub.add_parser(name, help=text)
        mode = hook.add_mutually_exclusive_group()
        mode.add_argument("--claude", action="store_true", help="Claude Code output")
        mode.add_argument("--cursor", action="store_true", help="Plain output (default)")


def run(args: argparse.Namespace) -> int:
    if args.command in ("hook-start", "hook-stop"):
        from orchestra.stage import hooks

        return hooks.run(args.command, hooks.CLAUDE if args.claude else hooks.CURSOR)
    from orchestra.canon.project import StoreBindingError, open_store
    from orchestra.canon.errors import StoreError

    from orchestra import views

    try:
        records = views.load_records(open_store(Path.cwd()))
        if args.command == "brief":
            text = views.render_brief(args.subject, records)
        else:
            name = "handoff" if args.command == "handoff" else args.name
            text = views.render_view(views.VIEWS[name], records, effort=args.effort)
    except (StoreBindingError, StoreError, views.ViewError) as exc:
        print(f"orchestra {args.command}: {exc}", file=sys.stderr)
        return 1
    print(text)
    return 0
