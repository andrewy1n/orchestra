"""Handler for `orchestra merge-evidence`."""

from __future__ import annotations

import argparse
import sys

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError
from orchestra.canon.workspace import Access, StoreNotReady
from orchestra.conductor import merge_evidence
from orchestra.conductor.cli.workspace import (
    command_dir,
    not_ready_message,
    print_json,
    resolve_workspace,
)


def run_merge_evidence(args: argparse.Namespace) -> int:
    start = command_dir(args).resolve()
    try:
        workspace = resolve_workspace(args.store, start, Access.WRITE)
        result = merge_evidence.refresh_recommendation(workspace.open(), args.phase)
    except StoreNotReady as exc:
        print(f"orchestra merge-evidence: {not_ready_message(exc, start)}", file=sys.stderr)
        return 2
    except (LookupError, OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        print(f"orchestra merge-evidence: {exc}", file=sys.stderr)
        return 2
    print_json(result)
    return 0 if result["recommendation"] == "ready" else 1
