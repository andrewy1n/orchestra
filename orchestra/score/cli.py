"""CLI wiring for `orchestra effort`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Protocol

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.workspace import Access, StoreNotReady, Workspace, not_ready_message
from orchestra.score import autonomy

COMMANDS = frozenset({"effort"})


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


def add_parsers(sub: SubparserGroup) -> None:
    effort = sub.add_parser("effort", help="Effort settings")
    effort_sub = effort.add_subparsers(dest="action", required=True)
    set_autonomy = effort_sub.add_parser(
        "autonomy", help="Set an effort's autonomy level, or migrate autonomy constraints"
    )
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


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2))


def _print_migration(report: autonomy.MigrationReport, *, as_json: bool) -> None:
    rows = [
        {"constraint": m.constraint, "effort": m.effort, "level": m.level} for m in report.mappings
    ]
    if as_json:
        _print_json(
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


def _cmd_effort_autonomy(args: argparse.Namespace) -> int:
    start = Path(args.cwd).expanduser() if args.cwd else Path.cwd()
    pinned = Path(args.store).expanduser() if args.store else None
    writes = not args.migrate or args.apply
    try:
        workspace = Workspace.resolve(
            start, store=pinned, access=Access.WRITE if writes else Access.READ
        )
        project = workspace.open()
        if args.migrate:
            _print_migration(
                autonomy.migrate(project, apply=bool(args.apply)), as_json=bool(args.json)
            )
            return 0
        if not args.effort or not args.level:
            print("orchestra effort autonomy: an effort and a level are required", file=sys.stderr)
            return 2
        record = autonomy.set_autonomy(project, args.effort, args.level)
    except StoreNotReady as exc:
        print(f"orchestra effort autonomy: {not_ready_message(exc, start)}", file=sys.stderr)
        return 2
    except (autonomy.AutonomyError, OSError, RuntimeError, StoreBindingError, StoreError) as exc:
        print(f"orchestra effort autonomy: {exc}", file=sys.stderr)
        return 2
    if args.json:
        _print_json({"effort": args.effort, "autonomy": args.level, "record": record["id"]})
    else:
        print(f"{args.effort}: autonomy {args.level}")
    return 0


def run(args: argparse.Namespace) -> int:
    return _cmd_effort_autonomy(args)
