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


def _cell(value: object) -> str:
    return "-" if value is None else str(value)


def run(args: argparse.Namespace) -> int:
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
