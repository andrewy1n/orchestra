from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


@dataclass(frozen=True)
class Command:
    name: str
    help: str
    configure: Callable[[argparse.ArgumentParser], None] | None = None
    handle: Callable[[argparse.Namespace], int] | None = None
    passthrough: bool = False
    children: tuple[Command, ...] = ()


class CommandError(Exception):
    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


def mount(sub: SubparserGroup, commands: Sequence[Command], parents: tuple[str, ...] = ()) -> None:
    for command in commands:
        parser = sub.add_parser(command.name, help=command.help)
        if command.configure is not None:
            command.configure(parser)
        path = (*parents, command.name)
        parser.set_defaults(
            handler=command.handle, passthrough=command.passthrough, command_path=path
        )
        if command.children:
            mount(parser.add_subparsers(required=True), command.children, path)


def _prefix(args: argparse.Namespace) -> str:
    path: tuple[str, ...] = getattr(args, "command_path", ())
    return " ".join(("orchestra", *path))


def run(args: argparse.Namespace, extra: Sequence[str] = ()) -> int:
    handler: Callable[[argparse.Namespace], int] = args.handler
    if getattr(args, "passthrough", False):
        args.extra = list(extra)
    try:
        return handler(args)
    except CommandError as error:
        return fail(args, error.message, error.exit_code)


def fail(args: argparse.Namespace, message: str, code: int = 2) -> int:
    print(f"{_prefix(args)}: {message}", file=sys.stderr)
    return code


def emit_json(payload: object, *, compact: bool = False) -> None:
    if compact:
        print(json.dumps(payload, separators=(",", ":")))
    else:
        print(json.dumps(payload, indent=2))
