from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from evals.seeded_defects.cases import DEFECT_KINDS, DEFECT_TYPES, KINDS
from evals.seeded_defects.trees import build_case_tree
from orchestra.canon.project import open_store
from orchestra.canon.types import JsonValue, Record
from orchestra.tools import Git, RunFn

SubParsers: TypeAlias = "argparse._SubParsersAction[argparse.ArgumentParser]"  # pyright: ignore[reportPrivateUsage]
COMMAND_TIMEOUT_SECONDS = 600
RECORD_TYPES = ("work-item", "acceptance", "specification")
DEAD_STATES = frozenset({"superseded", "withdrawn"})
HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


class ScaffoldError(Exception):
    pass


@dataclass(frozen=True)
class Hunk:
    path: str
    lines: list[str]
    whole: bool


def register(subparsers: SubParsers) -> None:
    parser = subparsers.add_parser("scaffold", help="create a case folder from a landed phase")
    parser.add_argument("--phase", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--kind", required=True, choices=KINDS)
    parser.add_argument("--defect-type", choices=DEFECT_TYPES)
    parser.add_argument("--hunk", type=int, default=0)
    parser.add_argument("--test")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--store-root", type=Path, default=Path.cwd())
    parser.add_argument("--expected-file", action="append", default=[])
    parser.add_argument("--expected-requirement-id", action="append", default=[])


def _is_test_path(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return path.startswith("tests/") or "/tests/" in path or name.startswith("test_")


def _string(value: JsonValue | None) -> str:
    return value if isinstance(value, str) else ""


def _frozen_records(store_root: Path, phase: str) -> list[dict[str, JsonValue]]:
    project = open_store(store_root, read_only=True)
    frozen: list[dict[str, JsonValue]] = []
    for short in RECORD_TYPES:
        for record in project.list(f"score:{short}"):
            if not _in_phase(record, phase) or record.get("lifecycle_state") in DEAD_STATES:
                continue
            frozen.append(_frozen(short, record))
    if not frozen:
        raise ScaffoldError(f"no records for phase {phase!r}")
    return frozen


def _in_phase(record: Record, phase: str) -> bool:
    payload = record.get("payload")
    return isinstance(payload, dict) and payload.get("phase") == phase


def _frozen(short: str, record: Record) -> dict[str, JsonValue]:
    payload = record.get("payload")
    fields = payload if isinstance(payload, dict) else {}
    item: dict[str, JsonValue] = {
        "record_type": short,
        "subject": _string(record.get("subject")),
        "body": _string(record.get("body")),
    }
    for key in ("title", "criterion", "verify_command"):
        value = _string(fields.get(key))
        if value and (key != "verify_command" or short == "acceptance"):
            item[key] = value
    return item


def _landed_hunks(diff: str) -> list[Hunk]:
    hunks: list[Hunk] = []
    path: str | None = None
    whole = False
    current: list[str] | None = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            path, whole, current = None, False, None
        elif line.startswith("--- ") and current is None:
            whole = line == "--- /dev/null"
            path = None if whole else line[len("--- a/") :]
        elif line.startswith("+++ ") and current is None:
            if line == "+++ /dev/null":
                whole = True
            else:
                path = line[len("+++ b/") :]
        elif line.startswith("@@") and path is not None:
            current = [line]
            hunks.append(Hunk(path, current, whole))
        elif current is not None:
            current.append(line)
    return hunks


def _reverse_hunk(hunk: Hunk) -> str:
    match = HUNK_HEADER.match(hunk.lines[0])
    if match is None:
        raise ScaffoldError(f"bad hunk header: {hunk.lines[0]}")
    old_start, old_len, new_start, new_len, tail = match.groups()
    old = old_start if old_len is None else f"{old_start},{old_len}"
    new = new_start if new_len is None else f"{new_start},{new_len}"
    out = [
        f"diff --git a/{hunk.path} b/{hunk.path}",
        f"--- a/{hunk.path}",
        f"+++ b/{hunk.path}",
        f"@@ -{new} +{old} @@{tail}",
    ]
    for line in hunk.lines[1:]:
        if line.startswith("+"):
            out.append("-" + line[1:])
        elif line.startswith("-"):
            out.append("+" + line[1:])
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def _reverted_change_patch(diff: str, index: int) -> tuple[str, str]:
    hunks = [h for h in _landed_hunks(diff) if not _is_test_path(h.path) and not h.whole]
    if not 0 <= index < len(hunks):
        raise ScaffoldError(f"hunk {index} out of range: {len(hunks)} non-test hunks")
    return _reverse_hunk(hunks[index]), hunks[index].path


def _function_span(source: str, name: str) -> tuple[int, int] | None:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            first = min([node.lineno, *(d.lineno for d in node.decorator_list)])
            return first, node.end_lineno or node.lineno
    return None


def _removed_test_patch(git: Git, commit: str, diff: str, test: str) -> tuple[str, str]:
    paths = dict.fromkeys(h.path for h in _landed_hunks(diff) if _is_test_path(h.path))
    for path in paths:
        if not path.endswith(".py"):
            continue
        source = git.text("show", f"{commit}:{path}")
        span = _function_span(source + "\n", test)
        if span is None:
            continue
        lines = (source + "\n").splitlines(keepends=True)
        kept = lines[: span[0] - 1] + lines[span[1] :]
        body = "".join(difflib.unified_diff(lines, kept, fromfile=f"a/{path}", tofile=f"b/{path}"))
        return f"diff --git a/{path} b/{path}\n{body}", path
    raise ScaffoldError(f"test {test!r} not found in a test file of the landed diff")


def _baseline(repo: Path, commit: str, commands: list[str]) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as scratch:
        tree = build_case_tree(repo, commit, None, Path(scratch) / "tree")
        results: dict[str, str] = {}
        for command in commands:
            try:
                done = subprocess.run(
                    command,
                    shell=True,
                    cwd=tree,
                    capture_output=True,
                    check=False,
                    timeout=COMMAND_TIMEOUT_SECONDS,
                )
                results[command] = "pass" if done.returncode == 0 else "fail"
            except subprocess.TimeoutExpired:
                results[command] = "fail"
        return results


def _scaffold(args: argparse.Namespace) -> None:
    kind: str = args.kind
    defect_type: str | None = args.defect_type
    repo: Path = args.repo
    commit: str = args.commit
    if kind in DEFECT_KINDS and defect_type not in DEFECT_TYPES:
        raise ScaffoldError("a defect case needs --defect-type")
    git = Git(repo)
    full = git.text("rev-parse", f"{commit}^{{commit}}")
    parent = git.text("rev-parse", f"{full}^")
    diff_bytes = len(git.text("diff", "--binary", parent, full).encode())
    landed = git.run("diff", parent, full).stdout
    records = _frozen_records(args.store_root, args.phase)
    patch: str | None = None
    touched: list[str] = list(args.expected_file)
    if kind != "control":
        if defect_type == "reverted-change":
            patch, path = _reverted_change_patch(landed, args.hunk)
        else:
            if not args.test:
                raise ScaffoldError("removed-test needs --test")
            patch, path = _removed_test_patch(git, full, landed, args.test)
        touched = touched or [path]
    commands = list(
        dict.fromkeys(str(r["verify_command"]) for r in records if "verify_command" in r)
    )
    baseline = _baseline(repo, full, commands)
    folder: Path = args.cases / args.case_id
    folder.mkdir(parents=True, exist_ok=True)
    meta: dict[str, JsonValue] = {
        "phase": args.phase,
        "revision": full,
        "kind": kind,
        "expected_files": list(touched) if kind != "control" else [],
        "expected_requirement_ids": list(args.expected_requirement_id),
        "diff_bytes": diff_bytes,
    }
    if defect_type is not None and kind != "control":
        meta["defect_type"] = defect_type
    if patch is not None:
        (folder / "defect.patch").write_text(patch)
    (folder / "records.json").write_text(json.dumps(records, indent=2) + "\n")
    (folder / "baseline.json").write_text(json.dumps(baseline, indent=2) + "\n")
    (folder / "case.json").write_text(json.dumps(meta, indent=2) + "\n")


def run(args: argparse.Namespace, run: RunFn, confirm: Callable[[str], bool]) -> int:
    try:
        _scaffold(args)
    except (ScaffoldError, OSError, subprocess.CalledProcessError) as exc:
        print(f"scaffold: {exc}", file=sys.stderr)
        return 1
    return 0
