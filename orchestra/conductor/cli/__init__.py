"""CLI wiring for the conductor verbs."""

from __future__ import annotations

import argparse

from orchestra.conductor.cli.check import run_check_command
from orchestra.conductor.cli.close import run_close, run_close_batch
from orchestra.conductor.cli.land import run_land
from orchestra.conductor.cli.merge_evidence import run_merge_evidence
from orchestra.conductor.cli.parsers import SubparserGroup, add_parsers
from orchestra.conductor.cli.phase_commands import run_analyze, run_gate, run_review_brief
from orchestra.conductor.cli.suite_commands import run_suite
from orchestra.conductor.cli.wave_commands import (
    BriefRenderer,
    install_brief_renderer,
    run_task,
    run_wave,
)
from orchestra.conductor.cli.workflow_commands import run_workflow

COMMANDS = frozenset(
    {
        "check",
        "suite",
        "gate",
        "analyze",
        "review-brief",
        "wave",
        "task",
        "land",
        "close",
        "close-batch",
        "workflow",
        "merge-evidence",
    }
)

__all__ = [
    "COMMANDS",
    "BriefRenderer",
    "SubparserGroup",
    "add_parsers",
    "install_brief_renderer",
    "run",
]


def run(args: argparse.Namespace) -> int:
    if args.command == "check":
        return run_check_command(args)
    if args.command == "suite":
        return run_suite(args)
    if args.command == "gate":
        return run_gate(args)
    if args.command == "analyze":
        return run_analyze(args)
    if args.command == "wave":
        return run_wave(args)
    if args.command == "task":
        return run_task(args)
    if args.command == "land":
        return run_land(args)
    if args.command == "merge-evidence":
        return run_merge_evidence(args)
    if args.command == "close":
        return run_close(args)
    if args.command == "close-batch":
        return run_close_batch(args)
    if args.command == "workflow":
        return run_workflow(args)
    return run_review_brief(args)
