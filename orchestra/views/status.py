"""CLI wiring for `orchestra status`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Protocol


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


def add_parser(sub: SubparserGroup) -> None:
    status = sub.add_parser("status", help="Print running, ready, and needs-you counts per effort")
    status.add_argument(
        "directory", nargs="?", default=None, help="Project directory (default: current directory)"
    )
    status.add_argument(
        "--count", action="store_true", help="Print only the merged needs-you count"
    )


def run(args: argparse.Namespace) -> int:
    from dashboard.backend.gates import landing_facts
    from dashboard.backend.snapshot import load_snapshot
    from dashboard.backend.store import ModelError, change_token
    from orchestra.canon.errors import StoreError
    from orchestra.canon.workspace import Access, StoreNotReady, Workspace, not_ready_message

    start = Path(args.directory) if args.directory else Path.cwd()
    try:
        target = Workspace.resolve(start, access=Access.READ).open()
        token = change_token(target)
        facts = {
            phase: fact
            for view in load_snapshot(target, token=token).efforts
            for phase, fact in landing_facts(view, target.project_root).items()
        }
        merged = load_snapshot(target, token=token, landing=facts)
    except StoreNotReady as exc:
        print(f"orchestra status: {not_ready_message(exc, start)}", file=sys.stderr)
        return 1
    except (StoreError, ModelError, OSError) as exc:
        print(f"orchestra status: {exc}", file=sys.stderr)
        return 1
    if args.count:
        print(sum(len(view.needs_you) for view in merged.efforts))
        return 0
    for view in merged.efforts:
        running = sum(task.status == "running" for task in view.tasks)
        ready = sum(task.status == "ready" for task in view.tasks)
        print(f"{view.effort}: running {running}, ready {ready}, needs-you {len(view.needs_you)}")
    return 0
