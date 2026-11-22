"""Shared option handling for the conductor verbs."""

from __future__ import annotations

import argparse
from pathlib import Path

from orchestra.canon.project import Project
from orchestra.canon.workspace import Access, open_for_command


def work_dir(args: argparse.Namespace) -> Path:
    return Path(args.cwd).expanduser() if args.cwd else Path.cwd()


def store_path(args: argparse.Namespace) -> Path | None:
    return Path(args.store).expanduser() if args.store else None


def open_project(
    args: argparse.Namespace, start: Path, access: Access, *, refused_exit: int = 2
) -> Project:
    return open_for_command(start, access, store=store_path(args), refused_exit=refused_exit)
