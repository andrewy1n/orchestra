"""CLI wiring for the conductor verbs."""

from __future__ import annotations

import argparse

from orchestra.conductor.cli.parsers import SubparserGroup, add_parsers
from orchestra.conductor.cli.phase_commands import run_analyze, run_gate, run_review_brief
from orchestra.conductor.cli.suite_commands import run_suite

COMMANDS = frozenset({"suite", "gate", "analyze", "review-brief"})

__all__ = ["COMMANDS", "SubparserGroup", "add_parsers", "run"]


def run(args: argparse.Namespace) -> int:
    if args.command == "suite":
        return run_suite(args)
    if args.command == "gate":
        return run_gate(args)
    if args.command == "analyze":
        return run_analyze(args)
    return run_review_brief(args)
