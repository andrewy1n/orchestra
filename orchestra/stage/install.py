"""Bridge from the ``orchestra`` CLI to the provider-matrix installer.

The installer is checkout-side, so the import is lazy: a pip-installed CLI
without ``installer/`` still serves every other subcommand.
"""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path


def main(args: Namespace) -> int:
    try:
        from installer.model import InstallRequest
        from installer.runner import run
    except ModuleNotFoundError as exc:  # pragma: no cover - packaging guard
        print(
            "orchestra install: the installer package is not available "
            f"({exc}); run this command from an orchestra checkout",
            file=sys.stderr,
        )
        return 2
    request = InstallRequest(
        only=tuple(args.only or ()),
        all_providers=bool(args.all),
        scope=args.scope,
        copy=bool(args.copy),
        dry_run=bool(args.dry_run),
        uninstall=bool(args.uninstall),
        home=Path(args.home).expanduser() if args.home else None,
        list_only=bool(args.list_only),
        interactive=bool(args.interactive),
        non_interactive=bool(args.non_interactive),
    )
    return run(request)
