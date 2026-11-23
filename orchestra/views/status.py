"""CLI wiring for `orchestra status`."""

from __future__ import annotations

import argparse
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.workspace import Access, open_for_command
from orchestra.tools.command_kit import Command, CommandError


def _configure(status: argparse.ArgumentParser) -> None:
    status.add_argument(
        "directory", nargs="?", default=None, help="Project directory (default: current directory)"
    )
    status.add_argument(
        "--count", action="store_true", help="Print only the merged needs-you count"
    )


def _status(args: argparse.Namespace) -> int:
    from dashboard.backend.gates import landing_facts
    from dashboard.backend.snapshot import load_snapshot
    from dashboard.backend.store import ModelError, change_token

    start = Path(args.directory) if args.directory else Path.cwd()
    target = open_for_command(start, Access.READ)
    try:
        token = change_token(target)
        facts = {
            phase: fact
            for view in load_snapshot(target, token=token).efforts
            for phase, fact in landing_facts(view, target.project_root).items()
        }
        merged = load_snapshot(target, token=token, landing=facts)
    except (StoreError, ModelError, OSError) as exc:
        raise CommandError(str(exc), 1) from exc
    if args.count:
        print(sum(len(view.needs_you) for view in merged.efforts))
        return 0
    for view in merged.efforts:
        running = sum(task.status == "running" for task in view.tasks)
        ready = sum(task.status == "ready" for task in view.tasks)
        print(f"{view.effort}: running {running}, ready {ready}, needs-you {len(view.needs_you)}")
    return 0


def commands() -> list[Command]:
    return [
        Command(
            "status",
            "Print running, ready, and needs-you counts per effort",
            configure=_configure,
            handle=_status,
        )
    ]
