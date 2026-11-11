"""CLI wiring for `orchestra metrics`."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Protocol


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


def add_parser(sub: SubparserGroup) -> None:
    metrics = sub.add_parser("metrics", help="Measure done phases from the store")
    verbs = metrics.add_subparsers(dest="metrics_command", required=True)
    phases = verbs.add_parser("phases", help="Print one row for each done phase")
    phases.add_argument("--effort", default=None, help="Only phases of this effort")
    phases.add_argument("--json", action="store_true", help="Print the rows as JSON")
    phases.add_argument("directory", nargs="?", default=None, help="Project directory")
    repairs = verbs.add_parser("repairs", help="List fix commits on main with their repair links")
    repairs.add_argument("--since", required=True, help="Only commits on or after this date")
    repairs.add_argument("directory", nargs="?", default=None, help="Project directory")


def _cell(value: object) -> str:
    return "-" if value is None else str(value)


def _run_repairs(args: argparse.Namespace) -> int:
    from orchestra.canon.errors import StoreError
    from orchestra.canon.project import StoreBindingError
    from orchestra.metrics.repairs import build_repair_rows
    from orchestra.tools.errors import ToolError

    try:
        rows = build_repair_rows(
            Path(args.directory) if args.directory else Path.cwd(), since=args.since
        )
    except (StoreBindingError, StoreError, ToolError, OSError) as exc:
        print(f"orchestra metrics: {exc}", file=sys.stderr)
        return 1
    for r in rows:
        print(f"{r.sha}\t{r.subject}\t{_cell(r.cause)}\t{_cell(r.phase)}")
    return 1 if any(r.cause is None for r in rows) else 0


def run(args: argparse.Namespace) -> int:
    if args.metrics_command == "repairs":
        return _run_repairs(args)
    from orchestra.canon.errors import StoreError
    from orchestra.canon.project import StoreBindingError
    from orchestra.metrics.phases import build_phase_rows

    try:
        rows = build_phase_rows(
            Path(args.directory) if args.directory else Path.cwd(), effort=args.effort
        )
    except (StoreBindingError, StoreError, OSError) as exc:
        print(f"orchestra metrics: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps([asdict(r) for r in rows], indent=2))
        return 0
    for r in rows:
        print(
            f"{r.phase}\t{r.effort}\t{_cell(r.weight)}\t{r.tasks}\t{_cell(r.landing_time)}"
            f"\t{_cell(r.landing_source)}\t{_cell(r.elapsed_seconds)}"
        )
        for column, reason in r.missing.items():
            print(f"  {column}: null ({reason})")
    return 0
