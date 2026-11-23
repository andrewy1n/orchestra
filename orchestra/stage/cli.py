from __future__ import annotations

import argparse

from orchestra.canon.store_commands import Recoverer, Scanner
from orchestra.stage import store_tools
from orchestra.tools.command_kit import Command


def _configure_install(install: argparse.ArgumentParser) -> None:
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


def store_operations() -> tuple[Scanner, Recoverer]:
    return store_tools.scan, store_tools.recover


def _configure_hook(hook: argparse.ArgumentParser) -> None:
    mode = hook.add_mutually_exclusive_group()
    mode.add_argument("--claude", action="store_true", help="Claude Code output")
    mode.add_argument("--cursor", action="store_true", help="Plain output (default)")


def _install(args: argparse.Namespace) -> int:
    from orchestra.stage.install import main as install_main

    return install_main(args)


def _hook(name: str, args: argparse.Namespace) -> int:
    from orchestra.stage import hooks

    return hooks.run(name, hooks.CLAUDE if args.claude else hooks.CURSOR)


def _hook_start(args: argparse.Namespace) -> int:
    return _hook("hook-start", args)


def _hook_stop(args: argparse.Namespace) -> int:
    return _hook("hook-stop", args)


def commands() -> list[Command]:
    return [
        Command(
            "install",
            "Install orchestra payload for one or more agent hosts",
            configure=_configure_install,
            handle=_install,
        ),
        Command(
            "hook-start",
            "SessionStart hook: inject the handoff",
            configure=_configure_hook,
            handle=_hook_start,
        ),
        Command(
            "hook-stop",
            "Stop hook: block on validation errors new this session",
            configure=_configure_hook,
            handle=_hook_stop,
        ),
    ]
