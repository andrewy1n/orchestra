"""Resolve the store workspace for the conductor verbs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from orchestra.canon.workspace import Access, Workspace, not_ready_message


def command_dir(args: argparse.Namespace) -> Path:
    return Path(args.cwd).expanduser() if args.cwd else Path.cwd()


def print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2))


def resolve_workspace(store: str | None, start: Path, access: Access) -> Workspace:
    pinned = Path(store).expanduser() if store else None
    return Workspace.resolve(start, store=pinned, access=access)


__all__ = ["command_dir", "not_ready_message", "print_json", "resolve_workspace"]
