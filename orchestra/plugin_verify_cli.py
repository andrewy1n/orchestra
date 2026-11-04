"""CLI for running and signing configured built-in verification plugins."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from orchestra.tuner.manifest import ManifestError
from orchestra.tuner.plugin_evidence import dispatch_signed_plugins
from orchestra.tuner.plugins import PluginContext


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orchestra verify plugins",
        description="Run configured built-in plugins and emit signed evidence.",
    )
    parser.add_argument("--cwd", default=None, help="Repository root (default: process cwd)")
    parser.add_argument("--stage", choices=("task", "phase", "milestone"), required=True)
    parser.add_argument("--revision", default="HEAD", help="Target commit (default: HEAD)")
    parser.add_argument("--test", action="append", default=[], dest="tests", metavar="NODE")
    parser.add_argument(
        "--review-output",
        default=None,
        help="Structured reviewer output path, or - to read it from stdin",
    )
    parser.add_argument("--key", required=True, help="SSH private key path for signing")
    args = parser.parse_args(argv)

    work = Path(args.cwd) if args.cwd else Path.cwd()
    try:
        reviewer_output = None
        if args.review_output == "-":
            reviewer_output = sys.stdin.read()
        elif args.review_output is not None:
            reviewer_output = Path(args.review_output).read_text(encoding="utf-8")
        evidence = dispatch_signed_plugins(
            PluginContext(
                root=work,
                stage=args.stage,
                revision=args.revision,
                tests=tuple(args.tests),
                reviewer_output=reviewer_output,
            ),
            key_path=args.key,
        )
    except (OSError, ValueError, ManifestError) as exc:
        print(exc, file=sys.stderr)
        return 2
    print(json.dumps([asdict(item) for item in evidence], separators=(",", ":")))
    return 0 if all(item.result == "pass" for item in evidence) else 1
