"""CLI wiring for the conductor verbs."""

from __future__ import annotations

import argparse

from orchestra.conductor.cli.close import run_close, run_close_batch
from orchestra.conductor.cli.land import run_land
from orchestra.conductor.cli.parsers import SubparserGroup, add_parsers
from orchestra.conductor.cli.phase_commands import run_analyze, run_gate, run_review_brief
from orchestra.conductor.cli.suite_commands import run_suite
from orchestra.conductor.cli.wave_commands import BriefRenderer, run_task, run_wave

COMMANDS = frozenset(
    {"suite", "gate", "analyze", "review-brief", "wave", "task", "land", "close", "close-batch"}
)

__all__ = ["COMMANDS", "SubparserGroup", "add_parsers", "run"]


def run(args: argparse.Namespace, *, render_brief: BriefRenderer) -> int:
    if args.command == "suite":
        return run_suite(args)
    if args.command == "gate":
        return run_gate(args)
    if args.command == "analyze":
        return run_analyze(args)
    if args.command == "wave":
        return run_wave(args, render_brief)
    if args.command == "task":
        return run_task(args)
    if args.command == "land":
        return run_land(args)
    if args.command == "close":
        return run_close(args)
    if args.command == "close-batch":
        return run_close_batch(args)
    return run_review_brief(args)
