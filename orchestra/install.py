"""Bridge from the ``orchestra`` CLI to the provider-matrix installer.

The installer is checkout-side, so the import is lazy: a pip-installed CLI
without ``installer/`` still serves every other subcommand.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main(args) -> int:
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
        global_scope=bool(args.global_),
        copy=bool(args.copy),
        dry_run=bool(args.dry_run),
        uninstall=bool(args.uninstall),
        home=Path(args.home).expanduser() if args.home else None,
    )
    return run(request)
