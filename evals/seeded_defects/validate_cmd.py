from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias

from evals.seeded_defects.cases import CaseSetError, load_case_set
from orchestra.tools import RunFn

SubParsers: TypeAlias = "argparse._SubParsersAction[argparse.ArgumentParser]"  # pyright: ignore[reportPrivateUsage]
DEFAULT_CASES = Path(__file__).parent / "cases"


def register(subparsers: SubParsers) -> None:
    parser = subparsers.add_parser("validate", help="validate a case set without a model call")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--repo", type=Path, default=Path.cwd())


def run(args: argparse.Namespace, run: RunFn, confirm: Callable[[str], bool]) -> int:
    try:
        cases = load_case_set(args.cases, args.repo)
    except CaseSetError as exc:
        for error in exc.errors:
            print(error, file=sys.stderr)
        return 1
    print(f"{len(cases)} cases valid")
    return 0
