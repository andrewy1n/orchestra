#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["fastapi", "uvicorn"]
# ///
"""Loopback FastAPI server for the project's artifact store.

Bind address is always 127.0.0.1 (``--host`` is accepted and ignored).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from dashboard.backend.server.app import create_app
from orchestra.canon.project import StoreBindingError
from orchestra.canon.workspace import Access, StoreNotReady, Workspace

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
        target = Workspace.resolve(Path.cwd(), access=Access.WRITE).open()
    except StoreNotReady as exc:
        searched = ", ".join(str(path) for path in exc.searched)
        print(f"store_not_ready: no store found; searched: {searched}", file=sys.stderr)
        return 1
    except StoreBindingError as exc:
        print(exc, file=sys.stderr)
        return 1

    import uvicorn

    uvicorn.run(create_app(target), host=HOST, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
