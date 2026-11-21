from __future__ import annotations

import argparse
from typing import Protocol

COMMANDS = frozenset({"hook-start", "hook-stop"})


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


def add_parsers(sub: SubparserGroup) -> None:
    for name, text in (
        ("hook-start", "SessionStart hook: inject the handoff"),
        ("hook-stop", "Stop hook: block on validation errors new this session"),
    ):
        hook = sub.add_parser(name, help=text)
        mode = hook.add_mutually_exclusive_group()
        mode.add_argument("--claude", action="store_true", help="Claude Code output")
        mode.add_argument("--cursor", action="store_true", help="Plain output (default)")


def run(args: argparse.Namespace) -> int:
    from orchestra.stage import hooks

    return hooks.run(args.command, hooks.CLAUDE if args.claude else hooks.CURSOR)
