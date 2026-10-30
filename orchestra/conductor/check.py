"""Implement `orchestra check`: run verify_command and write a check-run."""

from __future__ import annotations

import hashlib
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from orchestra.canon.git_backend import run_git
from orchestra.canon.project import StoreBindingError, open_store
from orchestra.canon.store import StoreError
from orchestra.canon.validation import ValidationError
from orchestra.conductor.policy import (
    dirty_pass_decision,
    manual_refuse_message,
    map_process_outcome,
)

RUNNER = "orchestra"
DEFAULT_TIMEOUT_S = 600.0
OUTPUT_BODY_CHARS = 8000


@dataclass
class CheckOutcome:
    exit_code: int
    stdout: str
    message: str = ""
    record: dict[str, Any] | None = None


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run_git(cwd, *args, capture_output=True, text=True)


def git_head(cwd: Path) -> str:
    result = _git(cwd, "rev-parse", "HEAD")
    if result.returncode != 0:
        raise RuntimeError(f"git rev-parse HEAD failed: {result.stderr or result.stdout}")
    return result.stdout.strip()


def git_is_dirty(cwd: Path) -> bool:
    result = _git(cwd, "status", "--porcelain")
    if result.returncode != 0:
        raise RuntimeError(f"git status failed: {result.stderr or result.stdout}")
    return bool(result.stdout.strip())


def git_diff_sha256(cwd: Path) -> str:
    """Hash of staged+unstaged diff plus untracked file paths (stable enough for flagging)."""
    diff = _git(cwd, "diff", "HEAD")
    porcelain = _git(cwd, "status", "--porcelain")
    blob = (diff.stdout or "") + "\n" + (porcelain.stdout or "")
    return hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest()


def run_verify_command(
    command: str,
    *,
    cwd: Path,
    timeout: float,
) -> tuple[int | None, float, str, bool, bool]:
    """Return (exit_code, duration_s, combined_output, timed_out, missing)."""
    started = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.monotonic() - started
        output = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, duration, output, False, False
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        out = ""
        if exc.stdout:
            out += exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode("utf-8", "replace")
        if exc.stderr:
            out += exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode("utf-8", "replace")
        out += f"\n[orchestra check] timed out after {timeout}s\n"
        return None, duration, out, True, False
    except FileNotFoundError:
        duration = time.monotonic() - started
        return None, duration, f"[orchestra check] command not found: {command!r}\n", False, True
    except OSError as exc:
        duration = time.monotonic() - started
        # shell=True usually absorbs missing binaries as non-zero; treat other OS errors as blocked
        return None, duration, f"[orchestra check] could not run command: {exc}\n", False, True


def _output_sha256(output: str) -> str:
    return hashlib.sha256(output.encode("utf-8", "replace")).hexdigest()


def _body_tail(output: str) -> str:
    if len(output) <= OUTPUT_BODY_CHARS:
        return output
    return output[-OUTPUT_BODY_CHARS:]


_NODE_ID_RE = re.compile(r"(?:FAILED|ERROR)\s+(\S+::\S+)")
_SUMMARY_NODE_RE = re.compile(
    r"^(?:FAILED|ERROR)\s+(\S+::\S+)",
    re.MULTILINE,
)


def parse_failing_node_ids(output: str) -> list[str]:
    """Extract pytest node ids from failure/error lines (stable order, unique)."""
    seen: set[str] = set()
    ordered: list[str] = []
    for match in _SUMMARY_NODE_RE.finditer(output or ""):
        node = match.group(1).strip()
        if node not in seen:
            seen.add(node)
            ordered.append(node)
    if ordered:
        return ordered
    for match in _NODE_ID_RE.finditer(output or ""):
        node = match.group(1).strip()
        if node not in seen:
            seen.add(node)
            ordered.append(node)
    return ordered


def run_check(
    *,
    acceptance_id: str,
    cwd: Path,
    store_root: Path | None = None,
    allow_dirty: bool = False,
    execution_report: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> CheckOutcome:
    work = cwd.resolve()
    try:
        project = open_store(store_root or Path.cwd())
    except StoreBindingError as exc:
        return CheckOutcome(exit_code=4, stdout="", message=str(exc))

    try:
        acceptance = project.get(acceptance_id, "score:acceptance")
    except StoreError as exc:
        return CheckOutcome(exit_code=4, stdout="", message=str(exc))

    payload = acceptance.get("payload") or {}
    method = payload.get("method") or ""
    if method == "manual":
        return CheckOutcome(
            exit_code=3,
            stdout="",
            message=manual_refuse_message(),
        )
    if method not in ("tdd", "check"):
        return CheckOutcome(
            exit_code=4,
            stdout="",
            message=f"Unsupported acceptance method {method!r}; expected tdd, check, or manual.",
        )

    verify_command = (payload.get("verify_command") or "").strip()
    if not verify_command:
        return CheckOutcome(
            exit_code=4,
            stdout="",
            message="Acceptance has an empty verify_command; nothing to run.",
        )

    try:
        head = git_head(work)
        dirty = git_is_dirty(work)
        diff_digest = git_diff_sha256(work) if dirty else None
    except RuntimeError as exc:
        return CheckOutcome(exit_code=4, stdout="", message=str(exc))

    exit_code, duration_s, output, timed_out, missing = run_verify_command(
        verify_command, cwd=work, timeout=timeout,
    )
    # shell=True: a missing binary often yields exit 127 rather than FileNotFoundError
    if exit_code == 127:
        missing = True
    result = map_process_outcome(exit_code=exit_code, timed_out=timed_out, missing=missing)

    decision = dirty_pass_decision(
        dirty=dirty,
        result=result,
        head=head,
        diff_sha256=diff_digest,
        allow_dirty=allow_dirty,
    )
    if decision.refuse:
        return CheckOutcome(exit_code=3, stdout="", message=decision.refuse_message)

    check_payload: dict[str, Any] = {
        "criterion_id": acceptance["id"],
        "revision": decision.revision,
        "result": result,
        "effort": payload.get("effort") or "",
        "method": method,
        "signed_by": "",
        "runner": RUNNER,
        "duration_s": round(duration_s, 6),
        "output_sha256": _output_sha256(output),
    }
    if exit_code is not None and not timed_out and not missing:
        check_payload["exit_code"] = exit_code
    elif exit_code is not None:
        check_payload["exit_code"] = exit_code
    if decision.diff_sha256:
        check_payload["diff_sha256"] = decision.diff_sha256
    if payload.get("requirement"):
        check_payload["requirement"] = payload["requirement"]
    if payload.get("evidence_kind"):
        check_payload["evidence_kind"] = payload["evidence_kind"]
    if result == "fail":
        failing_nodes = parse_failing_node_ids(output)
        if failing_nodes:
            check_payload["failing_node_ids"] = list(failing_nodes)

    informed_by = [acceptance["id"]]
    if execution_report:
        informed_by.append(execution_report)
    check_payload["informed_by"] = informed_by

    try:
        record = project.create(
            record_type="tuner:check-run",
            subject=acceptance.get("subject") or acceptance["id"],
            payload=check_payload,
            body=_body_tail(output),
        )
    except (StoreError, ValidationError, OSError) as exc:
        return CheckOutcome(exit_code=4, stdout="", message=str(exc))

    cli_exit = {"pass": 0, "fail": 1, "blocked": 2}[result]
    return CheckOutcome(
        exit_code=cli_exit,
        stdout="",
        message=f"check-run {record['id']} result={result} revision={decision.revision}",
        record=record,
    )
