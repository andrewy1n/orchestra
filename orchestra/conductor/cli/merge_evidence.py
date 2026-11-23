"""Handler for `orchestra merge-evidence`."""

from __future__ import annotations

import argparse

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.workspace import Access
from orchestra.conductor import merge_evidence
from orchestra.conductor.cli.options import open_project, work_dir
from orchestra.tools.command_kit import Command, CommandError, emit_json


def _configure(evidence: argparse.ArgumentParser) -> None:
    evidence.add_argument("--phase", required=True, help="Phase slug")
    evidence.add_argument("--cwd", default=None, help="Working directory (default: process cwd)")
    evidence.add_argument("--store", default=None, metavar="DIR", help="Store repo root")


def _handle(args: argparse.Namespace) -> int:
    start = work_dir(args).resolve()
    project = open_project(args, start, Access.WRITE)
    try:
        result = merge_evidence.refresh_recommendation(project, args.phase)
    except (LookupError, OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        raise CommandError(str(exc)) from exc
    emit_json(result)
    return 0 if result["recommendation"] == "ready" else 1


def commands() -> list[Command]:
    return [
        Command(
            "merge-evidence",
            "Refresh the CI evidence and show the merge recommendation",
            configure=_configure,
            handle=_handle,
        )
    ]
