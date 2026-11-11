from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias

from evals.seeded_defects.report import build_report
from orchestra.tools import RunFn

SubParsers: TypeAlias = "argparse._SubParsersAction[argparse.ArgumentParser]"  # pyright: ignore[reportPrivateUsage]
DEFAULT_CASES = Path(__file__).parent / "cases"


def register(subparsers: SubParsers) -> None:
    parser = subparsers.add_parser("report", help="report rates from a saved campaign")
    parser.add_argument("--campaign-dir", type=Path, required=True)
    parser.add_argument("--cases-dir", type=Path, default=DEFAULT_CASES)


def run(args: argparse.Namespace, run: RunFn, confirm: Callable[[str], bool]) -> int:
    print(build_report(args.campaign_dir, args.cases_dir), end="")
    return 0
