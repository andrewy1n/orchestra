"""CLI wiring for `orchestra effort`."""

from __future__ import annotations

import argparse
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.workspace import Access, open_for_command
from orchestra.score.planning import autonomy
from orchestra.tools.command_kit import Command, CommandError, emit_json


def _configure_autonomy(set_autonomy: argparse.ArgumentParser) -> None:
    set_autonomy.add_argument("effort", nargs="?", help="Effort slug")
    set_autonomy.add_argument("level", nargs="?", help="gated, auto-plan, or auto-phases")
    set_autonomy.add_argument(
        "--migrate", action="store_true", help="Map autonomy constraints to levels"
    )
    set_autonomy.add_argument(
        "--apply", action="store_true", help="With --migrate, write the changes"
    )
    set_autonomy.add_argument("--json", action="store_true", help="Print one JSON object")
    set_autonomy.add_argument(
        "--cwd", default=None, help="Directory inside the repo (default: cwd)"
    )
    set_autonomy.add_argument("--store", default=None, metavar="DIR", help="Store repo root")


def _print_migration(report: autonomy.MigrationReport, *, as_json: bool) -> None:
    rows = [
        {"constraint": m.constraint, "effort": m.effort, "level": m.level} for m in report.mappings
    ]
    if as_json:
        emit_json(
            {
                "mappings": rows,
                "notes": report.notes,
                "applied": report.applied,
                "levels": report.levels,
            }
        )
        return
    for row in rows:
        print(f"{row['constraint']}: {row['effort']} -> {row['level']}")
    for note in report.notes:
        print(note)
    print("applied" if report.applied else "dry run; pass --apply to write")


def _autonomy(args: argparse.Namespace) -> int:
    start = Path(args.cwd).expanduser() if args.cwd else Path.cwd()
    pinned = Path(args.store).expanduser() if args.store else None
    writes = not args.migrate or args.apply
    project = open_for_command(start, Access.WRITE if writes else Access.READ, store=pinned)
    try:
        if args.migrate:
            _print_migration(
                autonomy.migrate(project, apply=bool(args.apply)), as_json=bool(args.json)
            )
            return 0
        if not args.effort or not args.level:
            raise CommandError("an effort and a level are required")
        record = autonomy.set_autonomy(project, args.effort, args.level)
    except (autonomy.AutonomyError, OSError, RuntimeError, StoreBindingError, StoreError) as exc:
        raise CommandError(str(exc)) from exc
    if args.json:
        emit_json({"effort": args.effort, "autonomy": args.level, "record": record["id"]})
    else:
        print(f"{args.effort}: autonomy {args.level}")
    return 0


def commands() -> list[Command]:
    return [
        Command(
            "effort",
            "Effort settings",
            children=(
                Command(
                    "autonomy",
                    "Set an effort's autonomy level, or migrate autonomy constraints",
                    configure=_configure_autonomy,
                    handle=_autonomy,
                ),
            ),
        )
    ]
