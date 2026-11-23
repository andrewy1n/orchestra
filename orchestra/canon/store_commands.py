"""Parsers and handlers for `orchestra store`."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from orchestra.canon.backend import open_backend
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project, StoreBindingError, open_store
from orchestra.canon.sync import init_store
from orchestra.canon.types import JsonObject, Record
from orchestra.canon.validation import ValidationError
from orchestra.canon.workspace import Access, open_for_command
from orchestra.tools.command_kit import Command, CommandError, emit_json
from orchestra.tools.errors import ToolError
from orchestra.tools.git import Git

STORE_SCHEMAS = ("score", "conductor", "tuner")


@dataclass(frozen=True)
class StoreFinding:
    record_id: str
    record_type: str
    field: str
    message: str


@dataclass(frozen=True)
class RecoveryOutcome:
    report: JsonObject
    fresh_proof_required: bool


Scanner = Callable[[Sequence[Record]], list[StoreFinding]]
Recoverer = Callable[[Project, bool], RecoveryOutcome]


def _cwd(args: argparse.Namespace) -> Path:
    return Path(args.cwd).expanduser() if args.cwd else Path.cwd()


def _checkout_root(directory: Path) -> Path:
    if not directory.is_dir():
        return directory.resolve()
    try:
        return Git(directory).root()
    except ToolError as error:
        if error.returncode is None or type(error) is not ToolError:
            raise
        return directory.resolve()


def _flag_values(argv: list[str]) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    index = 0
    while index < len(argv):
        item = argv[index]
        if item.startswith("--") and index + 1 < len(argv) and not argv[index + 1].startswith("--"):
            values.setdefault(item, []).append(argv[index + 1])
            index += 2
        else:
            index += 1
    return values


def dispatch_store(project: Project, argv: list[str]) -> tuple[object, int]:
    verb = argv[0]
    flags = _flag_values(argv[1:])
    if verb == "list":
        record_type = (flags.get("--type") or [None])[0]
        if not record_type:
            raise ValueError("list requires --type")
        rows = project.list(record_type)
        state = (flags.get("--state") or [None])[0]
        if state:
            rows = [row for row in rows if row.get("lifecycle_state") == state]
        return {"records": rows, "count": len(rows)}, 0
    if verb == "get":
        record_id = (flags.get("--id") or [None])[0]
        if not record_id:
            raise ValueError("get requires --id")
        record_type = (flags.get("--type") or [None])[0]
        return project.get(record_id, record_type), 0
    if verb == "create":
        record_type = (flags.get("--type") or [None])[0]
        subject = (flags.get("--subject") or [None])[0]
        payload_text = (flags.get("--payload") or ["{}"])[0]
        body = (flags.get("--body") or [None])[0]
        if not record_type or not subject:
            raise ValueError("create requires --type and --subject")
        record = project.create(
            record_type=record_type,
            subject=subject,
            payload=json.loads(payload_text),
            body=body,
        )
        return {"ok": True, "op": "create", "record": record}, 0
    if verb == "apply":
        source = (flags.get("--file") or [None])[0]
        raw = Path(source).read_text(encoding="utf-8") if source else sys.stdin.read()
        operations = [json.loads(line) for line in raw.splitlines() if line.strip()]
        return project.apply(operations), 0
    raise ValueError(f"unsupported store operation {verb!r}")


def run_store_path(args: argparse.Namespace) -> int:
    try:
        project = open_for_command(_cwd(args), Access.READ)
    except (OSError, StoreBindingError) as exc:
        raise CommandError(str(exc)) from exc
    if args.json:
        emit_json(
            {
                "root": str(project.project_root),
                "store": str(project.store_path),
                "binding": project.binding.location,
            }
        )
    else:
        print(project.store_path)
    return 0


def run_store_scan(args: argparse.Namespace, scan: Scanner) -> int:
    project = open_for_command(_cwd(args), Access.READ)
    try:
        findings = scan(project.records())
    except (OSError, StoreBindingError, StoreError) as exc:
        raise CommandError(str(exc)) from exc
    for finding in findings:
        if args.json:
            print(json.dumps(asdict(finding)))
        else:
            print(f"{finding.record_id} {finding.record_type} {finding.field}: {finding.message}")
    return 1 if findings else 0


def run_store_recover(args: argparse.Namespace, recover: Recoverer) -> int:
    access = Access.WRITE if args.apply else Access.READ
    project = open_for_command(_cwd(args), access)
    try:
        outcome = recover(project, bool(args.apply))
    except (OSError, StoreBindingError, StoreError, ValidationError) as exc:
        raise CommandError(str(exc)) from exc
    emit_json(outcome.report)
    return 1 if outcome.fresh_proof_required else 0


def run_store_run(args: argparse.Namespace) -> int:
    argv = list(args.args)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        raise CommandError("needs library arguments")
    project = open_for_command(_cwd(args), Access.WRITE)
    try:
        payload, code = dispatch_store(project, argv)
    except (OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        raise CommandError(str(exc)) from exc
    text = payload if isinstance(payload, str) else json.dumps(payload)
    print(text, end="" if text.endswith("\n") else "\n")
    return code


def run_store_ensure(args: argparse.Namespace) -> int:
    root = _checkout_root(_cwd(args))
    artifacts = root / ".canon"
    try:
        project = open_store(root)
    except StoreBindingError:
        project = None
    except OSError as exc:
        raise CommandError(str(exc)) from exc
    if project is None:
        try:
            init_store(open_backend(artifacts), list(STORE_SCHEMAS))
            project = open_store(root)
        except (OSError, StoreError, StoreBindingError) as exc:
            raise CommandError(str(exc)) from exc
    payload = {
        "root": str(root),
        "artifacts": str(artifacts),
        "store": str(project.store_path),
        "store_ready": True,
    }
    if args.json:
        emit_json(payload)
    else:
        print(payload["store"])
    return 0


def _add_cwd(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cwd", default=None, help="Directory (default: cwd)")


def _configure_path(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the resolved root, store, and binding as JSON",
    )


def _configure_scan(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument("--json", action="store_true", help="Print one JSON object per finding")


def _configure_recover(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument("--apply", action="store_true", help="Apply recoverable changes")


def _configure_run(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="library arguments, after '--'",
    )


def _configure_ensure(parser: argparse.ArgumentParser) -> None:
    _add_cwd(parser)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the created paths and store readiness as JSON",
    )


def commands(*, scan: Scanner, recover: Recoverer) -> list[Command]:
    return [
        Command(
            "store",
            "Open the bound store and read or write it through the library",
            children=(
                Command(
                    "path",
                    "Print the resolved store path for a directory",
                    _configure_path,
                    run_store_path,
                ),
                Command(
                    "scan",
                    "Report phase, landing and proof packet records the typed readers reject",
                    _configure_scan,
                    lambda args: run_store_scan(args, scan),
                ),
                Command(
                    "recover-evidence",
                    "Inventory legacy evidence and recover attributable proof",
                    _configure_recover,
                    lambda args: run_store_recover(args, recover),
                ),
                Command(
                    "run",
                    "Run a library read or write against the opened store",
                    _configure_run,
                    run_store_run,
                ),
                Command(
                    "ensure",
                    "Create the store with the score, conductor, and tuner schemas when absent",
                    _configure_ensure,
                    run_store_ensure,
                ),
            ),
        )
    ]
