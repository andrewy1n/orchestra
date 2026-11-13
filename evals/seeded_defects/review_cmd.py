from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias

from evals.seeded_defects.campaign import run_campaign
from orchestra.tools import RunFn

SubParsers: TypeAlias = "argparse._SubParsersAction[argparse.ArgumentParser]"  # pyright: ignore[reportPrivateUsage]
DEFAULT_CASES = Path(__file__).parent / "cases"


def register(subparsers: SubParsers) -> None:
    parser = subparsers.add_parser("review", help="run the reviewer tier as a campaign")
    parser.add_argument("--model", required=True)
    parser.add_argument("--cases-dir", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--cases", nargs="+")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--campaign-dir", type=Path, required=True)


def run(args: argparse.Namespace, run: RunFn, confirm: Callable[[str], bool]) -> int:
    return run_campaign(args, run, confirm)
