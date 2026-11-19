from __future__ import annotations

import argparse
import importlib
import pkgutil
from collections.abc import Callable, Sequence
from types import ModuleType

import evals.seeded_defects as package
from orchestra.tools import RunFn

_SUFFIX = "_cmd"


def _verbs() -> dict[str, ModuleType]:
    table: dict[str, ModuleType] = {}
    for info in sorted(pkgutil.iter_modules(package.__path__), key=lambda i: i.name):
        if not info.name.endswith(_SUFFIX):
            continue
        name = f"{package.__name__}.{info.name}"
        try:
            table[info.name[: -len(_SUFFIX)]] = importlib.import_module(name)
        except ModuleNotFoundError as exc:
            if exc.name != name:
                raise
    return table


def main(argv: Sequence[str], *, run: RunFn, confirm: Callable[[str], bool]) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.seeded_defects")
    subparsers = parser.add_subparsers(dest="verb", required=True)
    table = _verbs()
    for module in table.values():
        module.register(subparsers)
    args = parser.parse_args(list(argv))
    return int(table[args.verb].run(args, run, confirm))


if __name__ == "__main__":
    import sys

    from orchestra.tools import run_subprocess

    raise SystemExit(
        main(
            sys.argv[1:],
            run=run_subprocess,
            confirm=lambda message: input(f"{message} [y/N] ").strip().lower() == "y",
        )
    )
