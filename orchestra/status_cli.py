"""CLI wiring for `orchestra status`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def add_parser(sub) -> None:
    status = sub.add_parser("status", help="Print running, ready, and needs-you counts per effort")
    status.add_argument(
        "directory", nargs="?", default=None, help="Project directory (default: current directory)"
    )
    status.add_argument(
        "--count", action="store_true", help="Print only the merged needs-you count"
    )


def run(args: argparse.Namespace) -> int:
    from dashboard.backend.gates import apply_landing_needs, landings_for_snapshot
    from dashboard.backend.snapshot import load_snapshot
    from dashboard.backend.store import ModelError
    from orchestra.canon.errors import StoreError
    from orchestra.canon.project import StoreBindingError, open_store

    try:
        target = open_store(Path(args.directory) if args.directory else Path.cwd())
        snapshot = load_snapshot(target)
        merged = apply_landing_needs(snapshot, landings_for_snapshot(target.project_root, snapshot))
    except (StoreBindingError, StoreError, ModelError, OSError) as exc:
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
