"""Parsers and handlers for `orchestra store`."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from orchestra.canon.backend import open_backend
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project, StoreBindingError, open_store
from orchestra.canon.sync import init_store
from orchestra.canon.types import JsonObject, Record
from orchestra.canon.validation import ValidationError
from orchestra.canon.workspace import Access, StoreNotReady, Workspace, not_ready_message
from orchestra.tools.errors import ToolError
from orchestra.tools.git import Git

STORE_SCHEMAS = ("score", "conductor", "tuner")
REFUSED_EXIT = 2


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


class SubparserGroup(Protocol):
    def add_parser(self, name: str, *, help: str) -> argparse.ArgumentParser: ...


def add_store_parser(sub: SubparserGroup) -> None:
    store = sub.add_parser(
        "store",
        help="Open the bound store and read or write it through the library",
    )
    store_sub = store.add_subparsers(dest="action", required=True)
    store_path = store_sub.add_parser(
        "path",
        help="Print the resolved store path for a directory",
    )
    store_path.add_argument("--cwd", default=None, help="Directory (default: cwd)")
    store_path.add_argument(
        "--json",
        action="store_true",
        help="Print the resolved root, store, and binding as JSON",
    )
    store_scan = store_sub.add_parser(
        "scan",
        help="Report phase, landing and proof packet records the typed readers reject",
    )
    store_scan.add_argument("--cwd", default=None, help="Directory (default: cwd)")
    store_scan.add_argument("--json", action="store_true", help="Print one JSON object per finding")
    recover = store_sub.add_parser(
        "recover-evidence", help="Inventory legacy evidence and recover attributable proof"
    )
    recover.add_argument("--cwd", default=None, help="Directory (default: cwd)")
    recover.add_argument("--apply", action="store_true", help="Apply recoverable changes")
    store_run = store_sub.add_parser(
        "run",
        help="Run a library read or write against the opened store",
    )
    store_run.add_argument("--cwd", default=None, help="Directory (default: cwd)")
    store_run.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="library arguments, after '--'",
    )
    store_ensure = store_sub.add_parser(
        "ensure",
        help="Create the store with the score, conductor, and tuner schemas when absent",
    )
    store_ensure.add_argument("--cwd", default=None, help="Directory (default: cwd)")
    store_ensure.add_argument(
        "--json",
        action="store_true",
        help="Print the created paths and store readiness as JSON",
    )


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


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2))


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


def _open(start: Path, access: Access) -> Project:
    return Workspace.resolve(start, access=access).open()


def run_store_path(args: argparse.Namespace) -> int:
    start = _cwd(args)
    try:
        project = _open(start, Access.READ)
    except StoreNotReady as exc:
        print(f"orchestra store path: {not_ready_message(exc, start)}", file=sys.stderr)
        return REFUSED_EXIT
    except (OSError, StoreBindingError) as exc:
        print(f"orchestra store path: {exc}", file=sys.stderr)
        return REFUSED_EXIT
    if args.json:
        _print_json(
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
    start = _cwd(args)
    try:
        findings = scan(_open(start, Access.READ).records())
    except StoreNotReady as exc:
        print(f"orchestra store scan: {not_ready_message(exc, start)}", file=sys.stderr)
        return REFUSED_EXIT
    except (OSError, StoreBindingError, StoreError) as exc:
        print(f"orchestra store scan: {exc}", file=sys.stderr)
        return REFUSED_EXIT
    for finding in findings:
        if args.json:
            print(json.dumps(asdict(finding)))
        else:
            print(f"{finding.record_id} {finding.record_type} {finding.field}: {finding.message}")
    return 1 if findings else 0


def run_store_recover(args: argparse.Namespace, recover: Recoverer) -> int:
    start = _cwd(args)
    access = Access.WRITE if args.apply else Access.READ
    try:
        outcome = recover(_open(start, access), bool(args.apply))
    except StoreNotReady as exc:
        print(f"orchestra store recover-evidence: {not_ready_message(exc, start)}", file=sys.stderr)
        return REFUSED_EXIT
    except (OSError, StoreBindingError, StoreError, ValidationError) as exc:
        print(f"orchestra store recover-evidence: {exc}", file=sys.stderr)
        return REFUSED_EXIT
    _print_json(outcome.report)
    return 1 if outcome.fresh_proof_required else 0


def run_store_run(args: argparse.Namespace) -> int:
    argv = list(args.args)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        print("orchestra store run: needs library arguments", file=sys.stderr)
        return REFUSED_EXIT
    start = _cwd(args)
    try:
        project = _open(start, Access.WRITE)
        payload, code = dispatch_store(project, argv)
    except StoreNotReady as exc:
        print(f"orchestra store run: {not_ready_message(exc, start)}", file=sys.stderr)
        return REFUSED_EXIT
    except (OSError, RuntimeError, StoreBindingError, StoreError, ValueError) as exc:
        print(f"orchestra store run: {exc}", file=sys.stderr)
        return REFUSED_EXIT
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
        print(f"orchestra store ensure: {exc}", file=sys.stderr)
        return REFUSED_EXIT
    if project is None:
        try:
            init_store(open_backend(artifacts), list(STORE_SCHEMAS))
            project = open_store(root)
        except (OSError, StoreError, StoreBindingError) as exc:
            print(f"orchestra store ensure: {exc}", file=sys.stderr)
            return REFUSED_EXIT
    payload = {
        "root": str(root),
        "artifacts": str(artifacts),
        "store": str(project.store_path),
        "store_ready": True,
    }
    if args.json:
        _print_json(payload)
    else:
        print(payload["store"])
    return 0


def run_store(args: argparse.Namespace, *, scan: Scanner, recover: Recoverer) -> int:
    if args.action == "recover-evidence":
        return run_store_recover(args, recover)
    if args.action == "path":
        return run_store_path(args)
    if args.action == "run":
        return run_store_run(args)
    if args.action == "scan":
        return run_store_scan(args, scan)
    return run_store_ensure(args)
