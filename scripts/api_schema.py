#!/usr/bin/env python3
"""Write or check the dashboard API's OpenAPI schema.

Usage:
    python3 scripts/api_schema.py
    python3 scripts/api_schema.py --check
    python3 scripts/api_schema.py --check --schema PATH
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_SCHEMA = ROOT / "dashboard" / "frontend" / "openapi.json"
REGENERATE = "python scripts/api_schema.py"


def render() -> str:
    from dashboard.backend.server.app import create_app
    from orchestra.canon.project import Binding, Project

    unbound = ROOT / ".api-schema-unbound"
    target = Project(project_root=unbound, store_path=unbound, binding=Binding(None, "api_schema"))
    document = create_app(target).openapi()
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail when the schema file differs from the live schema")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="schema file to write or check")
    args = parser.parse_args(argv)

    live = render()
    if not args.check:
        args.schema.write_text(live)
        print(f"wrote {args.schema}")
        return 0

    current = args.schema.read_text() if args.schema.is_file() else None
    if current == live:
        return 0
    print(
        f"api_schema.py: {args.schema} is out of date with the FastAPI app's OpenAPI schema.\n"
        f"Run `{REGENERATE}`, then `npm run api-types` in dashboard/frontend, and commit the result.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
