"""CLI wiring for the view commands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Protocol

from orchestra.views.render import render_brief

COMMANDS = frozenset({"handoff", "view", "brief"})


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


def add_parsers(sub: SubparserGroup) -> None:
    handoff = sub.add_parser("handoff", help="Print the handoff markdown")
    handoff.add_argument("--effort", default=None, help="Limit to one effort slug")
    view = sub.add_parser("view", help="Print a derived view as markdown")
    view.add_argument("name", choices=("plan", "status", "verification", "roadmap"))
    view.add_argument("--effort", default=None, help="Limit to one effort slug")
    brief = sub.add_parser("brief", help="Print one work-item's brief")
    brief.add_argument("subject", help="Work-item subject")


def run(args: argparse.Namespace) -> int:
    from orchestra.canon.errors import StoreError
    from orchestra.canon.project_config import ProjectConfigError
    from orchestra.canon.workspace import Access, StoreNotReady, Workspace, not_ready_message
    from orchestra.conductor.phase_progress import PhaseProgressError, open_phase_progress
    from orchestra.views import render as views

    start = Path.cwd()
    try:
        project = Workspace.resolve(start, access=Access.READ).open()
        records = views.load_records(project)
        if args.command == "brief":
            text = render_brief(args.subject, records)
        else:
            name = "handoff" if args.command == "handoff" else args.name
            is_handoff = args.command == "handoff"
            text = views.render_view(
                views.VIEWS[name],
                records,
                effort=args.effort,
                statuses=views.effort_statuses(records) if is_handoff else None,
                landing=views.landing_facts(records, project.project_root) if is_handoff else None,
                progress=open_phase_progress(project, records),
                root=project.project_root,
            )
    except StoreNotReady as exc:
        print(f"orchestra {args.command}: {not_ready_message(exc, start)}", file=sys.stderr)
        return 1
    except (
        StoreError,
        views.ViewError,
        ProjectConfigError,
        PhaseProgressError,
    ) as exc:
        print(f"orchestra {args.command}: {exc}", file=sys.stderr)
        return 1
    print(text)
    return 0
