"""Resolve the store workspace for the conductor verbs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from orchestra.canon.workspace import Access, StoreNotReady, Workspace


def command_dir(args: argparse.Namespace) -> Path:
    return Path(args.cwd).expanduser() if args.cwd else Path.cwd()


def print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2))


def resolve_workspace(store: str | None, start: Path, access: Access) -> Workspace:
    pinned = Path(store).expanduser() if store else None
    return Workspace.resolve(start, store=pinned, access=access)


def not_ready_message(error: StoreNotReady, start: Path) -> str:
    searched = ", ".join(str(path) for path in error.searched)
    return f"store_not_ready: No artifact store for {start.resolve()}; searched: {searched}"
