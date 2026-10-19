#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn", "textual>=0.80"]
# ///
"""Loopback FastAPI server for the project's artifact store.

Bind address is always 127.0.0.1 (``--host`` is accepted and ignored).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from dashboard.artifact_store import StoreBindingError, resolve  # noqa: E402
from dashboard.web.app import create_app  # noqa: E402

HOST = "127.0.0.1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Orchestra web dashboard")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--host",
        default=HOST,
        help="Ignored; the server always binds 127.0.0.1.",
    )
    args = parser.parse_args(argv)

    try:
        target = resolve(Path.cwd())
    except StoreBindingError as exc:
        print(exc, file=sys.stderr)
        return 1
    if target.store is None:
        print(
            f"No artifact store for {target.root}.\n"
            f"No store binding and no meta.json in:\n"
            f"  {target.repo_store()} (local)\n"
            f"  {target.home_store()} (global)\n"
            f"Set SE_WORKFLOW_STORE or add .artifacts/store-binding.json "
            f'with {{"store":"local"}} or {{"store":"global"}}.',
            file=sys.stderr,
        )
        return 1

    import uvicorn

    uvicorn.run(create_app(target), host=HOST, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
