from __future__ import annotations

import argparse
from typing import Protocol

COMMANDS = frozenset({"hook-start", "hook-stop", "install"})


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


def _add_install_parser(sub: SubparserGroup) -> None:
    install = sub.add_parser(
        "install",
        help="Install orchestra payload for one or more agent hosts",
    )
    install.add_argument(
        "--only",
        action="append",
        metavar="HOST",
        default=[],
        help=("Install only this provider id; repeat for more (default: detected hosts)"),
    )
    install.add_argument(
        "--all",
        action="store_true",
        help="Select every provider in the matrix",
    )
    scope = install.add_mutually_exclusive_group()
    scope.add_argument(
        "--scope",
        choices=("project", "global"),
        default=None,
        help="Install into the project or the user directories",
    )
    scope.add_argument(
        "--global",
        dest="scope",
        action="store_const",
        const="global",
        help="Alias for --scope global",
    )
    install.add_argument(
        "--list",
        "-l",
        dest="list_only",
        action="store_true",
        help="Print the provider matrix with project/global detection",
    )
    install.add_argument(
        "--copy",
        action="store_true",
        help="Copy payload instead of symlinking to this checkout",
    )
    install.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and write nothing",
    )
    install.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove exactly what the adapter registered",
    )
    interactive = install.add_mutually_exclusive_group()
    interactive.add_argument(
        "--interactive",
        action="store_true",
        help="Force the host wizard even when standard input is not a TTY",
    )
    interactive.add_argument(
        "--non-interactive",
        "--yes",
        "-y",
        dest="non_interactive",
        action="store_true",
        help="Never prompt; use --only/--all or detected hosts",
    )
    install.add_argument(
        "--home",
        default=None,
        metavar="DIR",
        help="Redirect the whole install under DIR (tests, throwaway homes)",
    )


def add_parsers(sub: SubparserGroup) -> None:
    _add_install_parser(sub)
    for name, text in (
        ("hook-start", "SessionStart hook: inject the handoff"),
        ("hook-stop", "Stop hook: block on validation errors new this session"),
    ):
        hook = sub.add_parser(name, help=text)
        mode = hook.add_mutually_exclusive_group()
        mode.add_argument("--claude", action="store_true", help="Claude Code output")
        mode.add_argument("--cursor", action="store_true", help="Plain output (default)")


def run(args: argparse.Namespace) -> int:
    if args.command == "install":
        from orchestra.stage.install import main as install_main

        return install_main(args)
    from orchestra.stage import hooks

    return hooks.run(args.command, hooks.CLAUDE if args.claude else hooks.CURSOR)
