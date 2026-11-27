"""Implement `orchestra check`: run verify_command and write a check-run."""

from __future__ import annotations

import hashlib
import re
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.canon.validation import ValidationError
from orchestra.conductor.model_types import PlanningPayload
from orchestra.conductor.verification.policy import (
    dirty_pass_decision,
    manual_refuse_message,
    map_process_outcome,
)
from orchestra.conductor.verification.standing_constraints import (
    criterion_id,
    pinned_constraint_ids,
)
from orchestra.score.planning.phase import current_phase_model
from orchestra.score.planning.standing_constraint import (
    RECORD_TYPE as STANDING_CONSTRAINT,
)
from orchestra.score.planning.standing_constraint import read_standing_constraint
from orchestra.tools import Git

ProposedConstraintReader = Callable[[Sequence[Record], str, str], Record | None]

RUNNER = "orchestra"
DEFAULT_TIMEOUT_S = 600.0
OUTPUT_BODY_CHARS = 8000
_CLI_EXIT = {"pass": 0, "fail": 1, "blocked": 2}


@dataclass
class CheckOutcome:
    exit_code: int
    stdout: str
    message: str = ""
    record: Record | None = None
    reused: bool = False


def git_is_dirty(cwd: Path, *, all_untracked: bool = False) -> bool:
    status_flags = ("--untracked-files=all",) if all_untracked else ()
    result = Git(cwd).run("status", "--porcelain", *status_flags)
    if result.returncode != 0:
        raise RuntimeError(f"git status failed: {result.stderr or result.stdout}")
    return bool(result.stdout.strip())


def _candidate_has_hidden_paths(git: Git) -> bool:
    entries = git.text("ls-files", "-v", "-z").split("\0")
    return any(entry and (entry[0] == "S" or entry[0].islower()) for entry in entries)


def git_diff_sha256(cwd: Path) -> str:
    """Hash of staged+unstaged diff plus untracked file paths (stable enough for flagging)."""
    git = Git(cwd)
    diff = git.run("diff", "HEAD")
    porcelain = git.run("status", "--porcelain")
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
        # nosemgrep: orchestra.shell-true -- verify_command intentionally executes shell programs from the work contract.
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
            out += (
                exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode("utf-8", "replace")
            )
        if exc.stderr:
            out += (
                exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode("utf-8", "replace")
            )
        out += f"\n[orchestra check] timed out after {timeout}s\n"
        return None, duration, out, True, False
    except FileNotFoundError:
        duration = time.monotonic() - started
        return None, duration, f"[orchestra check] command not found: {command!r}\n", False, True
    except OSError as exc:
        duration = time.monotonic() - started
        # shell=True usually absorbs missing binaries as non-zero; treat other OS errors as blocked
        return None, duration, f"[orchestra check] could not run command: {exc}\n", False, True


def output_sha256(output: str) -> str:
    return hashlib.sha256(output.encode("utf-8", "replace")).hexdigest()


def _body_tail(output: str) -> str:
    if len(output) <= OUTPUT_BODY_CHARS:
        return output
    return output[-OUTPUT_BODY_CHARS:]


_BALANCED = r"\[(?:[^\[\]]|\[[^\[\]]*\])*\]"
_BRACKETED = rf"[^\s:\[]+(?:::[^\s:\[]+)+(?:{_BALANCED}|\[.*?\])?(?= - |[ \t]*\r?$)"
_NODE = rf"({_BRACKETED}|\S+::\S+)"
_NODE_ID_RE = re.compile(rf"(?:FAILED|ERROR)\s+{_NODE}", re.MULTILINE)
_SUMMARY_NODE_RE = re.compile(rf"^(?:FAILED|ERROR)\s+{_NODE}", re.MULTILINE)


def parse_failing_node_ids(output: str) -> list[str]:
    """Extract pytest node ids from failure/error lines (stable order, unique).

    Brackets balance to two levels; a deeper or unbalanced parameter falls back to the first
    closing bracket followed by a separator.
    """
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


def _find_identical_check_run(
    project: Project,
    *,
    acceptance: Record,
    revision: str,
    result: str,
) -> Record | None:
    records = project.records()
    corrected = {
        record_id
        for record_id, values in project.derived(records).items()
        if values.get("corrected")
    }
    matches = [
        record
        for record in records
        if record["record_type"] == "tuner:check-run"
        and record["lifecycle_state"] not in ("superseded", "retracted")
        and record["id"] not in corrected
        and record["payload"].get("criterion_id") == acceptance["id"]
        and record["payload"].get("revision") == revision
        and isinstance(provenance := record.get("provenance"), dict)
        and provenance.get("acceptance_revision") == acceptance["revision"]
    ]
    if not matches:
        return None
    newest = max(record["recorded_at"] for record in matches)
    latest = [record for record in matches if record["recorded_at"] == newest]
    if any(record["payload"].get("result") != result for record in latest):
        return None
    return latest[0]


def run_check(
    *,
    acceptance_id: str,
    cwd: Path,
    project: Project,
    allow_dirty: bool = False,
    execution_report: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> CheckOutcome:
    work = cwd.resolve()
    try:
        acceptance = project.get(acceptance_id, "score:acceptance")
    except StoreError as exc:
        return CheckOutcome(exit_code=4, stdout="", message=str(exc))

    payload: PlanningPayload = acceptance.get("payload") or {}  # pyright: ignore[reportAssignmentType]  # Acceptance schemas validate these payload fields.
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

    return _execute(
        verify_command,
        work=work,
        project=project,
        allow_dirty=allow_dirty,
        timeout=timeout,
        criterion=acceptance["id"],
        subject=acceptance.get("subject") or acceptance["id"],
        effort=payload.get("effort") or "",
        method=method,
        provenance_revision=acceptance["revision"],
        informed_by=[acceptance["id"], *([execution_report] if execution_report else [])],
        extra=_acceptance_extra(payload),
        reuse=lambda revision, result: _find_identical_check_run(
            project, acceptance=acceptance, revision=revision, result=result
        ),
    )


def _acceptance_extra(payload: PlanningPayload) -> JsonObject:
    extra: JsonObject = {}
    if payload.get("requirement"):
        extra["requirement"] = payload["requirement"]  # pyright: ignore[reportTypedDictNotRequiredAccess]  # The truthy field check establishes presence.
    if payload.get("evidence_kind"):
        extra["evidence_kind"] = payload["evidence_kind"]  # pyright: ignore[reportTypedDictNotRequiredAccess]  # The truthy field check establishes presence.
    return extra


def run_standing_constraint_check(
    *,
    name: str,
    phase: str,
    cwd: Path,
    project: Project,
    allow_dirty: bool = False,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> CheckOutcome:
    records = project.records()
    pinned = None
    effort = ""
    for design in records:
        if (
            design["record_type"] == "score:design"
            and design["lifecycle_state"] == "active"
            and design["payload"].get("phase") == phase
        ):
            effort = str(design["payload"].get("effort") or effort)
    for pinned_id in pinned_constraint_ids(records, phase):
        candidate = next((r for r in records if r["id"] == pinned_id), None)
        if (
            candidate is not None
            and candidate["record_type"] == STANDING_CONSTRAINT
            and candidate["subject"] == name
        ):
            pinned = candidate
            break
    if pinned is None:
        return CheckOutcome(
            exit_code=4,
            stdout="",
            message=f"Standing constraint {name!r} is not pinned by phase {phase!r}.",
        )
    return _run_constraint(pinned, name, effort, cwd, project, allow_dirty, timeout)


def run_proposed_constraint_check(
    *,
    change_id: str,
    phase: str,
    cwd: Path,
    project: Project,
    reader: ProposedConstraintReader,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> CheckOutcome:
    records = project.records()
    try:
        pinned = reader(records, phase, change_id)
        phase_model = current_phase_model(phase, records)
    except StoreError as exc:
        return CheckOutcome(4, "", str(exc))
    if pinned is None or phase_model is None:
        return CheckOutcome(4, "", f"No checkable proposed constraint {change_id!r} for {phase!r}.")
    return _run_constraint(
        pinned,
        pinned["subject"],
        phase_model.effort,
        cwd,
        project,
        False,
        timeout,
        require_clean_revision=True,
    )


def _run_constraint(
    pinned: Record,
    name: str,
    effort: str,
    cwd: Path,
    project: Project,
    allow_dirty: bool,
    timeout: float,
    *,
    require_clean_revision: bool = False,
) -> CheckOutcome:
    try:
        constraint = read_standing_constraint(pinned)
    except StoreError as exc:
        return CheckOutcome(exit_code=4, stdout="", message=str(exc))
    return _execute(
        constraint.check,
        work=cwd.resolve(),
        project=project,
        allow_dirty=allow_dirty,
        timeout=timeout,
        criterion=criterion_id(pinned["id"]),
        subject=f"{name}-check",
        effort=effort,
        method="check",
        provenance_revision=pinned["revision"],
        informed_by=[],
        extra={},
        reuse=lambda _revision, _result: None,
        require_clean_revision=require_clean_revision,
    )


def _execute(
    verify_command: str,
    *,
    work: Path,
    project: Project,
    allow_dirty: bool,
    timeout: float,
    criterion: str,
    subject: str,
    effort: str,
    method: str,
    provenance_revision: str,
    informed_by: list[str],
    extra: JsonObject,
    reuse: Callable[[str, str], Record | None],
    require_clean_revision: bool = False,
) -> CheckOutcome:
    git = Git(work)
    try:
        head = git.head()
        dirty = git_is_dirty(work, all_untracked=require_clean_revision)
        if require_clean_revision and dirty:
            return CheckOutcome(
                3, "", "A proposed constraint check requires a clean candidate worktree."
            )
        if require_clean_revision and _candidate_has_hidden_paths(git):
            return CheckOutcome(
                3, "", "A proposed constraint check requires a complete candidate checkout."
            )
        diff_digest = git_diff_sha256(work) if dirty else None
    except RuntimeError as exc:
        return CheckOutcome(exit_code=4, stdout="", message=str(exc))

    exit_code, duration_s, output, timed_out, missing = run_verify_command(
        verify_command,
        cwd=work,
        timeout=timeout,
    )
    if require_clean_revision:
        try:
            changed = (
                git.head() != head
                or git_is_dirty(work, all_untracked=True)
                or _candidate_has_hidden_paths(git)
            )
        except RuntimeError as exc:
            return CheckOutcome(4, "", str(exc))
        if changed:
            return CheckOutcome(
                3, "", "The candidate worktree changed during the proposed constraint check."
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

    if decision.revision != "dirty":
        try:
            existing = reuse(decision.revision, result)
        except (StoreError, OSError) as exc:
            return CheckOutcome(exit_code=4, stdout="", message=str(exc))
        if existing is not None:
            return CheckOutcome(
                exit_code=_CLI_EXIT[result],
                stdout="",
                message=f"check-run {existing['id']} reused result={result} "
                f"revision={decision.revision}",
                record=existing,
                reused=True,
            )

    check_payload: JsonObject = {
        "criterion_id": criterion,
        "revision": decision.revision,
        "result": result,
        "effort": effort,
        "method": method,
        "signed_by": "",
        "runner": RUNNER,
        "duration_s": round(duration_s, 6),
        "output_sha256": output_sha256(output),
    }
    if exit_code is not None:
        check_payload["exit_code"] = exit_code
    if decision.diff_sha256:
        check_payload["diff_sha256"] = decision.diff_sha256
    check_payload.update(extra)
    if result == "fail":
        failing_nodes = parse_failing_node_ids(output)
        if failing_nodes:
            failing_node_values: list[JsonValue] = []
            failing_node_values.extend(failing_nodes)
            check_payload["failing_node_ids"] = failing_node_values

    informed_by_values: list[JsonValue] = [*informed_by]
    check_payload["informed_by"] = informed_by_values

    try:
        record = project.create(
            record_type="tuner:check-run",
            subject=subject,
            payload=check_payload,
            body=_body_tail(output),
            provenance={"acceptance_revision": provenance_revision},
        )
    except (StoreError, ValidationError, OSError) as exc:
        return CheckOutcome(exit_code=4, stdout="", message=str(exc))

    return CheckOutcome(
        exit_code=_CLI_EXIT[result],
        stdout="",
        message=f"check-run {record['id']} result={result} revision={decision.revision}",
        record=record,
    )
