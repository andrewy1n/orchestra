"""CLI wiring for `orchestra metrics`."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.workspace import Access, open_for_command
from orchestra.metrics.compare import UnknownBoundaryError, compare_phases, render_text
from orchestra.metrics.phases import build_phase_rows
from orchestra.metrics.repairs import build_repair_rows
from orchestra.tools.command_kit import Command, CommandError, emit_json
from orchestra.tools.errors import ToolError


def _configure_phases(phases: argparse.ArgumentParser) -> None:
    phases.add_argument("--effort", default=None, help="Only phases of this effort")
    phases.add_argument("--json", action="store_true", help="Print the rows as JSON")
    phases.add_argument("directory", nargs="?", default=None, help="Project directory")


def _configure_repairs(repairs: argparse.ArgumentParser) -> None:
    repairs.add_argument("--since", required=True, help="Only commits on or after this date")
    repairs.add_argument("directory", nargs="?", default=None, help="Project directory")


def _configure_compare(compare: argparse.ArgumentParser) -> None:
    compare.add_argument("boundary", help="Phase whose landing time splits the done phases")
    compare.add_argument("--json", action="store_true", help="Print the comparison as JSON")
    compare.add_argument("directory", nargs="?", default=None, help="Project directory")


def _cell(value: object) -> str:
    return "-" if value is None else str(value)


def _root(args: argparse.Namespace) -> Path:
    start = Path(args.directory) if args.directory else Path.cwd()
    return open_for_command(start, Access.READ).project_root


def _repairs(args: argparse.Namespace) -> int:
    root = _root(args)
    try:
        rows = build_repair_rows(root, since=args.since)
    except (StoreBindingError, StoreError, ToolError, OSError) as exc:
        raise CommandError(str(exc), 1) from exc
    for r in rows:
        print(f"{r.sha}\t{r.subject}\t{_cell(r.cause)}\t{_cell(r.phase)}")
    return 1 if any(r.cause is None for r in rows) else 0


def _compare(args: argparse.Namespace) -> int:
    root = _root(args)
    try:
        comparison = compare_phases(root, args.boundary)
    except (StoreBindingError, StoreError, UnknownBoundaryError, OSError) as exc:
        raise CommandError(str(exc), 1) from exc
    if args.json:
        emit_json(comparison)
    else:
        print(render_text(comparison))
    return 0


def _phases(args: argparse.Namespace) -> int:
    root = _root(args)
    try:
        rows = build_phase_rows(root, effort=args.effort)
    except (StoreBindingError, StoreError, OSError) as exc:
        raise CommandError(str(exc), 1) from exc
    if args.json:
        emit_json([asdict(r) for r in rows])
        return 0
    for r in rows:
        print(
            f"{r.phase}\t{r.effort}\t{_cell(r.weight)}\t{r.tasks}\t{_cell(r.landing_time)}"
            f"\t{_cell(r.landing_source)}\t{_cell(r.elapsed_seconds)}"
        )
        for column, reason in r.missing.items():
            print(f"  {column}: null ({reason})")
    return 0


def commands() -> list[Command]:
    return [
        Command(
            "metrics",
            "Measure done phases from the store",
            children=(
                Command(
                    "phases",
                    "Print one row for each done phase",
                    configure=_configure_phases,
                    handle=_phases,
                ),
                Command(
                    "repairs",
                    "List fix commits on main with their repair links",
                    configure=_configure_repairs,
                    handle=_repairs,
                ),
                Command(
                    "compare",
                    "Compare done phases before and after a phase",
                    configure=_configure_compare,
                    handle=_compare,
                ),
            ),
        )
    ]
