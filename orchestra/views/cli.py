"""CLI wiring for the view commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project_config import ProjectConfigError
from orchestra.canon.workspace import Access, open_for_command
from orchestra.conductor.phases.progress.phase_progress import (
    PhaseProgressError,
    open_phase_progress,
)
from orchestra.tools.command_kit import Command, CommandError
from orchestra.views import render as views
from orchestra.views.render import render_brief

__all__ = ["commands", "render_brief"]


def _configure_handoff(handoff: argparse.ArgumentParser) -> None:
    handoff.add_argument("--effort", default=None, help="Limit to one effort slug")


def _configure_view(view: argparse.ArgumentParser) -> None:
    view.add_argument("name", choices=("plan", "status", "verification", "roadmap"))
    view.add_argument("--effort", default=None, help="Limit to one effort slug")


def _configure_brief(brief: argparse.ArgumentParser) -> None:
    brief.add_argument("subject", help="Work-item subject")


def _handoff(args: argparse.Namespace) -> int:
    project = open_for_command(Path.cwd(), Access.READ)
    try:
        records = views.load_records(project)
        text = views.render_view(
            views.VIEWS["handoff"],
            records,
            effort=args.effort,
            statuses=views.effort_statuses(records),
            landing=views.landing_facts(records, project.project_root),
            progress=open_phase_progress(project, records),
            root=project.project_root,
        )
    except (StoreError, views.ViewError, ProjectConfigError, PhaseProgressError) as exc:
        raise CommandError(str(exc), 1) from exc
    print(text)
    return 0


def _view(args: argparse.Namespace) -> int:
    project = open_for_command(Path.cwd(), Access.READ)
    try:
        records = views.load_records(project)
        text = views.render_view(
            views.VIEWS[args.name],
            records,
            effort=args.effort,
            statuses=None,
            landing=None,
            progress=open_phase_progress(project, records),
            root=project.project_root,
        )
    except (StoreError, views.ViewError, ProjectConfigError, PhaseProgressError) as exc:
        raise CommandError(str(exc), 1) from exc
    print(text)
    return 0


def _brief(args: argparse.Namespace) -> int:
    project = open_for_command(Path.cwd(), Access.READ)
    try:
        text = render_brief(args.subject, views.load_records(project))
    except (StoreError, views.ViewError, ProjectConfigError, PhaseProgressError) as exc:
        raise CommandError(str(exc), 1) from exc
    print(text)
    return 0


def commands() -> list[Command]:
    return [
        Command(
            "handoff", "Print the handoff markdown", configure=_configure_handoff, handle=_handoff
        ),
        Command(
            "view", "Print a derived view as markdown", configure=_configure_view, handle=_view
        ),
        Command("brief", "Print one work-item's brief", configure=_configure_brief, handle=_brief),
    ]
