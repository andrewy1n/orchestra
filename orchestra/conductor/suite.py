"""Phase-level suite runner: policy, background worker, check-run, gate, fix routing.

Parent session loads ``[suite]`` from ``orchestra.toml``, starts the
configured command in a detached worker in the phase worktree when mode is
smoke/full, polls for completion, and records one ``tuner:check-run`` with
``evidence_kind: integration`` and subject ``<phase>-suite``. Does not
fix-and-rerun inline. Suite is never red-first.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import re
import sys
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError, open_store
from orchestra.canon.project_config import load_project_config
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.canon.validation import ValidationError
from orchestra.conductor.check import (
    OUTPUT_BODY_CHARS,
    RUNNER,
    git_head,
    output_sha256,
    parse_failing_node_ids,
)
from orchestra.conductor.policy import dirty_pass_decision, map_process_outcome
from orchestra.conductor.revision import revision_matches as _revision_matches
from orchestra.tools import CliTool, Git, ToolError

EVIDENCE_KIND = "integration"
SUBJECT_SUFFIX = "-suite"
METHOD = "check"

SKIPPED_EXIT_CODE = 4


@dataclass(frozen=True)
class SuitePolicy:
    """Configured project suite policy after consumer defaults are applied."""

    mode: str = "none"
    command: str = ""
    gate: str = "required"
    source_path: str | None = None

    @property
    def run_locally(self) -> bool:
        """True when verify should start the suite in the worktree."""
        if self.mode in ("none", ""):
            return False
        if self.gate == "deferred":
            return False
        if self.mode == "external":
            return False
        if self.mode in ("smoke", "full"):
            return bool(self.command.strip())
        return False

    @property
    def blocks_merge(self) -> bool:
        """True when missing/failing suite at head blocks Landing merge."""
        if self.mode in ("none", ""):
            return False
        return self.gate == "required"

    @property
    def advisory(self) -> bool:
        return self.gate == "advisory" and self.mode not in ("none", "")

    @property
    def deferred_landing_stop(self) -> bool:
        """Deferred gate: Landing human stop; do not run locally."""
        return self.gate == "deferred" and self.mode not in ("none", "")

    @property
    def create_fix_tasks_on_fail(self) -> bool:
        """Fix-task storms only when the gate is required."""
        return self.blocks_merge and self.run_locally


def load_suite_policy(start: Path | None = None) -> SuitePolicy:
    """Load the required suite policy from the project root config."""
    root = start or Path.cwd()
    suite_config = load_project_config(root).suite
    return SuitePolicy(
        mode=suite_config.mode,
        command=suite_config.command,
        gate=suite_config.gate,
        source_path=str(root / "orchestra.toml"),
    )


def suite_subject(phase_slug: str) -> str:
    slug = (phase_slug or "").strip()
    if not slug:
        raise ValueError("phase_slug is required")
    if slug.endswith(SUBJECT_SUFFIX):
        return slug
    return f"{slug}{SUBJECT_SUFFIX}"


def is_suite_subject(subject: str) -> bool:
    text = (subject or "").strip()
    return text.endswith(SUBJECT_SUFFIX)


def cluster_by_module(node_ids: Sequence[str]) -> dict[str, list[str]]:
    """Cluster node ids by test file / module path (text before ``::``)."""
    clusters: dict[str, list[str]] = {}
    for node in node_ids:
        module = node.split("::", 1)[0] if "::" in node else node
        clusters.setdefault(module, []).append(node)
    return clusters


def module_fix_subject(module: str) -> str:
    """Stable fix work-item subject for a failing module path."""
    cleaned = module.strip().replace("\\", "/")
    if cleaned.startswith("tests/"):
        cleaned = cleaned[len("tests/") :]
    if cleaned.endswith(".py"):
        cleaned = cleaned[:-3]
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", cleaned).strip("-")
    return f"fix-{cleaned}"


@dataclass
class SuiteFixRouting:
    clusters: dict[str, list[str]] = field(default_factory=dict)
    fix_subjects: list[str] = field(default_factory=list)
    create_fix_flags: list[bool] = field(default_factory=list)
    escalate: bool = False
    reopen_done: bool = False
    inline_fix_and_rerun: bool = False


def route_suite_failures(
    node_ids: Sequence[str],
    *,
    fix_budget_remaining: int,
    policy: SuitePolicy | None = None,
) -> SuiteFixRouting:
    """Create fix-task subjects clustered by module under the retry budget.

    Never reopens ``done``. Never implies an inline verifier fix-and-rerun.
    When gate is advisory (or suite does not block), creates no fix tasks.
    """
    if policy is not None and not policy.create_fix_tasks_on_fail:
        clusters = cluster_by_module(list(node_ids))
        return SuiteFixRouting(
            clusters=clusters,
            fix_subjects=[""] * len(clusters),
            create_fix_flags=[False] * len(clusters),
            escalate=False,
            reopen_done=False,
            inline_fix_and_rerun=False,
        )
    clusters = cluster_by_module(list(node_ids))
    modules = list(clusters.keys())
    remaining = max(0, int(fix_budget_remaining))
    flags: list[bool] = []
    subjects: list[str] = []
    for module in modules:
        subject = module_fix_subject(module)
        if remaining > 0:
            flags.append(True)
            subjects.append(subject)
            remaining -= 1
        else:
            flags.append(False)
            subjects.append("")
    escalate = bool(modules) and not any(flags)
    if sum(flags) < len(modules) and any(flags):
        escalate = True
    return SuiteFixRouting(
        clusters=clusters,
        fix_subjects=subjects,
        create_fix_flags=flags,
        escalate=escalate,
        reopen_done=False,
        inline_fix_and_rerun=False,
    )


def should_rerun_suite(*, fix_tasks_created: int) -> bool:
    """After fix tasks land, suite is expected to rerun at the new head."""
    return bool(fix_tasks_created)


def advisory_finding_payload(
    *,
    phase_slug: str,
    effort: str,
    suite: SuiteResult,
) -> JsonObject:
    """Finding payload for an advisory suite fail (does not block merge)."""
    subject = suite_subject(phase_slug)
    nodes = ", ".join(suite.failing_node_ids[:8]) if suite.failing_node_ids else "(see check-run)"
    return {
        "claim": f"advisory suite fail for {subject} at {suite.revision}",
        "basis": f"exit_code={suite.exit_code}; failing: {nodes}",
        "invalidated_when": ("suite check-run passes at phase head, or human clears the finding"),
        "effort": effort,
        "phase": phase_slug,
        "needs": "none",
    }


def _body_tail(output: str) -> str:
    if len(output) <= OUTPUT_BODY_CHARS:
        return output
    return output[-OUTPUT_BODY_CHARS:]


@dataclass
class SuiteStart:
    """Non-blocking start handle for a background suite job."""

    session_name: str
    worktree: Path
    phase_slug: str
    phase_head: str
    log_path: Path
    exit_path: Path
    started_monotonic: float
    blocking: bool = False
    skipped: bool = False
    skip_reason: str = ""
    policy: SuitePolicy | None = None
    run_id: str = ""
    run_dir: Path | None = None
    request_path: Path | None = None
    ready_path: Path | None = None
    result_path: Path | None = None
    lifecycle_path: Path | None = None
    skip_path: Path | None = None
    cancel_path: Path | None = None
    start_head: str = ""
    start_diff_sha256: str | None = None


@dataclass
class SuiteResult:
    exit_code: int
    duration_s: float
    output: str
    output_sha256: str
    failing_node_ids: list[str]
    result: str
    revision: str
    diff_sha256: str | None = None
    refuse: bool = False
    refuse_message: str = ""
    skipped: bool = False
    skip_reason: str = ""
    run_id: str = ""
    reason: str = ""
    worktree: Path | None = None
    start_head: str = ""
    start_diff_sha256: str | None = None


def resolve_suite_revision(
    cwd: Path,
    *,
    allow_dirty: bool = False,
    provisional_result: str = "pass",
) -> tuple[str, str | None, str | None]:
    """Return (revision, diff_sha256|None, refuse_message|None).

    Dirty pass is refused without ``allow_dirty``, matching check dirty policy.
    """
    head, diff = _suite_tree_identity(cwd)
    dirty = diff is not None
    decision = dirty_pass_decision(
        dirty=dirty,
        result=provisional_result,  # type: ignore[arg-type]
        head=head,
        diff_sha256=diff,
        allow_dirty=allow_dirty,
    )
    if decision.refuse:
        return decision.revision, decision.diff_sha256, decision.refuse_message
    return decision.revision, decision.diff_sha256, None


def suite_worktree_matches(worktree: Path, head: str, diff_sha256: str | None) -> bool:
    current_head, current_diff = _suite_tree_identity(worktree)
    return current_head == head and current_diff == diff_sha256


def _suite_tree_identity(worktree: Path) -> tuple[str, str | None]:
    git = Git(worktree)
    paths = ("--", ".", ":(exclude).suite")
    diff = git.run("diff", "HEAD", *paths)
    status = git.run("status", "--porcelain", "--untracked-files=all", *paths)
    if diff.returncode != 0 or status.returncode != 0:
        raise RuntimeError(f"cannot inspect suite worktree at {worktree}")
    if not status.stdout.strip():
        return git_head(worktree), None
    blob = diff.stdout + "\n" + status.stdout
    return git_head(worktree), hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest()


def read_suite_json_object(path: Path) -> JsonObject:
    try:
        value: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"invalid suite run metadata at {path}: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid suite run metadata at {path}: expected an object")
    return value


def validate_suite_request_version(request: Mapping[str, JsonValue], path: Path) -> None:
    version = request.get("version")
    if version is None:
        raise RuntimeError(f"invalid suite run metadata at {path}: missing version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise RuntimeError(f"invalid suite run metadata at {path}: invalid version")
    if version != 1:
        raise RuntimeError(f"invalid suite run metadata at {path}: unsupported version")


def atomic_write_suite_json(path: Path, value: Mapping[str, JsonValue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def _job_directory(worktree: Path, session_name: str) -> Path:
    job_id = hashlib.sha256(session_name.encode("utf-8")).hexdigest()
    return worktree / ".suite" / "jobs" / job_id


def _run_paths(run_dir: Path) -> dict[str, Path]:
    return {
        "request_path": run_dir / "request.json",
        "worker_log_path": run_dir / "worker.log",
        "output_path": run_dir / "output.log",
        "ready_path": run_dir / "ready.json",
        "result_path": run_dir / "result.json",
        "exit_path": run_dir / "exit",
        "lifecycle_path": run_dir / "worker.lock",
        "cancel_path": run_dir / "cancel.json",
    }


def load_suite_job(
    *,
    worktree: Path,
    phase_slug: str,
    session_name: str | None = None,
    run_id: str | None = None,
) -> SuiteStart:
    work = worktree.resolve()
    slug = phase_slug.strip()
    name = session_name or f"orchestra-suite-{slug}"
    job_dir = _job_directory(work, name)
    current_path = job_dir / "current.json"
    skipped_path = job_dir / "skipped.json"
    if not current_path.is_file():
        if skipped_path.is_file():
            skipped = read_suite_json_object(skipped_path)
            reason = skipped.get("reason")
            head = skipped.get("phase_head")
            if not isinstance(reason, str) or not isinstance(head, str):
                raise RuntimeError(f"invalid suite run metadata at {skipped_path}")
            return SuiteStart(
                session_name=name,
                worktree=work,
                phase_slug=slug,
                phase_head=head,
                log_path=job_dir / "output.log",
                exit_path=job_dir / "exit",
                started_monotonic=time.monotonic(),
                skipped=True,
                skip_reason=reason,
                skip_path=skipped_path,
            )
        legacy_log = work / ".suite" / f"{name}.log"
        legacy_exit = work / ".suite" / f"{name}.exit"
        if legacy_log.exists() or legacy_exit.exists():
            raise RuntimeError("legacy suite artifacts cannot prove a run; start a fresh suite run")
        raise RuntimeError(f"no suite run found for job {name!r}")
    pointer = read_suite_json_object(current_path)
    selected = run_id or pointer.get("run_id")
    if not isinstance(selected, str):
        raise RuntimeError(f"invalid suite run metadata at {current_path}: missing run_id")
    try:
        normalized = uuid.UUID(selected).hex
    except ValueError as error:
        raise RuntimeError(
            f"invalid suite run metadata at {current_path}: invalid run_id"
        ) from error
    if normalized != selected:
        raise RuntimeError(f"invalid suite run metadata at {current_path}: invalid run_id")
    run_dir = job_dir / "runs" / selected
    paths = _run_paths(run_dir)
    request = read_suite_json_object(paths["request_path"])
    validate_suite_request_version(request, paths["request_path"])
    required_text = ("session_name", "phase_slug", "worktree", "command", "phase_head", "revision")
    for field_name in required_text:
        if not isinstance(request.get(field_name), str):
            raise RuntimeError(
                f"invalid suite run metadata at {paths['request_path']}: missing {field_name}"
            )
    if request["session_name"] != name or request["phase_slug"] != slug:
        raise RuntimeError(f"invalid suite run metadata at {paths['request_path']}: job mismatch")
    if Path(str(request["worktree"])).resolve() != work:
        raise RuntimeError(
            f"invalid suite run metadata at {paths['request_path']}: worktree mismatch"
        )
    if request.get("run_id") != selected or not str(request.get("command", "")).strip():
        raise RuntimeError(
            f"invalid suite run metadata at {paths['request_path']}: invalid run request"
        )
    created = request.get("created_at_epoch")
    if not isinstance(created, (float, int)):
        raise RuntimeError(
            f"invalid suite run metadata at {paths['request_path']}: missing creation time"
        )
    start_head = request.get("start_head")
    start_diff = request.get("start_diff_sha256")
    if not isinstance(start_head, str) or (
        start_diff is not None and not isinstance(start_diff, str)
    ):
        raise RuntimeError(
            f"invalid suite run metadata at {paths['request_path']}: invalid starting revision"
        )
    saved_paths = request.get("paths")
    if not isinstance(saved_paths, dict) or any(
        saved_paths.get(key) != str(path) for key, path in paths.items()
    ):
        raise RuntimeError(f"invalid suite run metadata at {paths['request_path']}: invalid paths")
    return SuiteStart(
        session_name=name,
        worktree=work,
        phase_slug=slug,
        phase_head=str(request["phase_head"]),
        log_path=paths["output_path"],
        exit_path=paths["exit_path"],
        started_monotonic=time.monotonic() - max(0.0, time.time() - float(created)),
        run_id=selected,
        run_dir=run_dir,
        request_path=paths["request_path"],
        ready_path=paths["ready_path"],
        result_path=paths["result_path"],
        lifecycle_path=paths["lifecycle_path"],
        cancel_path=paths["cancel_path"],
        start_head=start_head,
        start_diff_sha256=start_diff,
    )


def _active_run(job_dir: Path) -> bool:
    pointer_path = job_dir / "current.json"
    if not pointer_path.is_file():
        return False
    pointer = read_suite_json_object(pointer_path)
    run_id = pointer.get("run_id")
    if not isinstance(run_id, str):
        raise RuntimeError(f"invalid suite run metadata at {pointer_path}: missing run_id")
    try:
        normalized = uuid.UUID(run_id).hex
    except ValueError as error:
        raise RuntimeError(
            f"invalid suite run metadata at {pointer_path}: invalid run_id"
        ) from error
    if normalized != run_id:
        raise RuntimeError(f"invalid suite run metadata at {pointer_path}: invalid run_id")
    run_dir = job_dir / "runs" / run_id
    result_path = _run_paths(run_dir)["result_path"]
    if result_path.is_file():
        read_suite_json_object(result_path)
        return False
    lock_path = _run_paths(run_dir)["lifecycle_path"]
    if not lock_path.is_file():
        raise RuntimeError(f"invalid suite run metadata: missing lifecycle lock at {lock_path}")
    descriptor = os.open(lock_path, os.O_RDWR)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        return False
    finally:
        os.close(descriptor)


def start_suite_background(
    *,
    worktree: Path,
    phase_slug: str,
    phase_head: str | None = None,
    session_name: str | None = None,
    log_dir: Path | None = None,
    suite_command: str | None = None,
    policy: SuitePolicy | None = None,
    allow_dirty: bool = False,
    timeout: float | None = None,
) -> SuiteStart | SuiteResult:
    """Start the suite in a detached worker; return after worker readiness.

    When policy says not to run locally (mode=none/external, gate=deferred),
    returns a ``SuiteStart`` with ``skipped=True`` and does not start a worker.
    On dirty-pass refusal, returns a ``SuiteResult`` with ``refuse=True``.
    """
    work = worktree.resolve()
    resolved_policy = policy if policy is not None else load_suite_policy(work)
    head = phase_head or git_head(work)

    slug = phase_slug.strip()
    name = session_name or f"orchestra-suite-{slug}"
    job_dir = _job_directory(work, name)
    skip_path = job_dir / "skipped.json"

    if not resolved_policy.run_locally:
        reason = f"suite skipped (mode={resolved_policy.mode}, gate={resolved_policy.gate})"
        atomic_write_suite_json(skip_path, {"phase_head": head, "reason": reason})
        return SuiteStart(
            session_name=name,
            worktree=work,
            phase_slug=slug,
            phase_head=head,
            log_path=job_dir / "output.log",
            exit_path=job_dir / "exit",
            started_monotonic=time.monotonic(),
            blocking=False,
            skipped=True,
            skip_reason=reason,
            policy=resolved_policy,
            skip_path=skip_path,
        )

    revision, diff, refuse_msg = resolve_suite_revision(
        work,
        allow_dirty=allow_dirty,
        provisional_result="pass",
    )
    if refuse_msg:
        return SuiteResult(
            exit_code=3,
            duration_s=0.0,
            output="",
            output_sha256=output_sha256(""),
            failing_node_ids=[],
            result="blocked",
            revision=revision,
            refuse=True,
            refuse_message=refuse_msg,
        )

    cmd = suite_command if suite_command is not None else resolved_policy.command
    if not cmd.strip():
        raise ValueError("suite command must be non-empty")
    if timeout is not None and (not math.isfinite(timeout) or timeout <= 0):
        raise ValueError("suite timeout must be a positive finite number")
    job_dir.mkdir(parents=True, exist_ok=True)
    guard_path = job_dir / "job.lock"
    with guard_path.open("a+b") as guard:
        fcntl.flock(guard.fileno(), fcntl.LOCK_EX)
        if _active_run(job_dir):
            raise RuntimeError(f"active suite run already exists for job {name!r}")
        run_id = uuid.uuid4().hex
        run_dir = job_dir / "runs" / run_id
        run_dir.mkdir(parents=True)
        paths = _run_paths(run_dir)
        request: JsonObject = {
            "version": 1,
            "run_id": run_id,
            "session_name": name,
            "phase_slug": slug,
            "worktree": str(work),
            "command": cmd,
            "phase_head": head,
            "revision": revision,
            "diff_sha256": diff,
            "start_head": git_head(work),
            "start_diff_sha256": diff,
            "created_at_epoch": time.time(),
            "timeout_seconds": timeout,
            "paths": {key: str(path) for key, path in paths.items()},
        }
        atomic_write_suite_json(paths["request_path"], request)
        paths["output_path"].touch()
        paths["exit_path"].touch()
        paths["lifecycle_path"].touch()
        atomic_write_suite_json(job_dir / "current.json", {"run_id": run_id})
        lifecycle_fd = os.open(paths["lifecycle_path"], os.O_RDWR)
        fcntl.flock(lifecycle_fd, fcntl.LOCK_EX)
        try:
            with paths["worker_log_path"].open("ab", buffering=0) as worker_log:
                process = CliTool(work).start_process(
                    [
                        sys.executable,
                        "-m",
                        "orchestra.conductor.suite_worker",
                        str(paths["request_path"]),
                        str(lifecycle_fd),
                    ],
                    cwd=work,
                    stdout=worker_log,
                    stderr=worker_log,
                    pass_fds=[lifecycle_fd],
                )
        except ToolError as error:
            fcntl.flock(lifecycle_fd, fcntl.LOCK_UN)
            os.close(lifecycle_fd)
            raise RuntimeError(
                f"cannot start suite worker; diagnostics: {paths['worker_log_path']}: {error}"
            ) from error
        os.close(lifecycle_fd)
    started = load_suite_job(
        worktree=work,
        phase_slug=slug,
        session_name=name,
        run_id=run_id,
    )
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if started.ready_path is not None and started.ready_path.is_file():
            return started
        if started.result_path is not None and started.result_path.is_file():
            result = read_suite_json_object(started.result_path)
            reason = result.get("reason")
            raise RuntimeError(
                f"suite worker failed to start: {reason}; inspect {paths['worker_log_path']}"
            )
        time.sleep(0.02)
    process.terminate_group()
    raise RuntimeError(
        f"suite worker did not become ready within 5 seconds; inspect {paths['worker_log_path']}"
    )


def suite_job_finished(job: SuiteStart) -> bool:
    if job.skipped:
        return True
    if job.result_path is None or job.lifecycle_path is None:
        raise RuntimeError("suite run metadata is missing its result or lifecycle path")
    return job.result_path.is_file() or not _lock_is_held(job.lifecycle_path)


def _lock_is_held(path: Path) -> bool:
    if not path.is_file():
        raise RuntimeError(f"invalid suite run metadata: missing lifecycle lock at {path}")
    descriptor = os.open(path, os.O_RDWR)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        return False
    finally:
        os.close(descriptor)


def _interrupted_result(job: SuiteStart, *, allow_dirty: bool) -> SuiteResult:
    if not job.log_path.is_file():
        raise RuntimeError(f"required suite output is missing at {job.log_path}")
    output = job.log_path.read_text(encoding="utf-8", errors="replace")
    revision, diff, _ = resolve_suite_revision(
        job.worktree,
        allow_dirty=allow_dirty,
        provisional_result="blocked",
    )
    return SuiteResult(
        exit_code=3,
        duration_s=max(0.0, time.monotonic() - job.started_monotonic),
        output=output,
        output_sha256=output_sha256(output),
        failing_node_ids=[],
        result="blocked",
        revision=revision,
        diff_sha256=diff,
        run_id=job.run_id,
        reason="interrupted",
        worktree=job.worktree,
        start_head=job.start_head,
        start_diff_sha256=job.start_diff_sha256,
    )


def _revision_changed_result(job: SuiteStart, output: str, duration: float) -> SuiteResult:
    return SuiteResult(
        exit_code=3,
        duration_s=round(max(0.0, duration), 6),
        output=output,
        output_sha256=output_sha256(output),
        failing_node_ids=[],
        result="blocked",
        revision="dirty" if job.start_diff_sha256 else job.start_head,
        diff_sha256=job.start_diff_sha256,
        run_id=job.run_id,
        reason="revision_changed",
        worktree=job.worktree,
        start_head=job.start_head,
        start_diff_sha256=job.start_diff_sha256,
    )


def cancel_suite_run(job: SuiteStart) -> str:
    if job.skipped:
        return "skipped"
    if job.cancel_path is None or job.result_path is None or job.lifecycle_path is None:
        raise RuntimeError("suite run metadata is missing cancellation paths")
    job_dir = job.run_dir.parent.parent if job.run_dir is not None else None
    if job_dir is None:
        raise RuntimeError("suite run metadata is missing its run directory")
    guard_path = job_dir / "job.lock"
    with guard_path.open("a+b") as guard:
        fcntl.flock(guard.fileno(), fcntl.LOCK_EX)
        if job.result_path.is_file():
            terminal = read_suite_json_object(job.result_path)
            reason = terminal.get("reason")
            return reason if isinstance(reason, str) else "completed"
        if not _lock_is_held(job.lifecycle_path):
            return "interrupted"
        if job.cancel_path.is_file():
            request = read_suite_json_object(job.cancel_path)
            if request.get("run_id") != job.run_id:
                raise RuntimeError(f"invalid cancellation metadata at {job.cancel_path}")
            reason = request.get("reason")
            return reason if isinstance(reason, str) else "cancelled"
        atomic_write_suite_json(
            job.cancel_path,
            {"run_id": job.run_id, "reason": "cancelled", "requested_at_epoch": time.time()},
        )
    return "requested"


def poll_suite(
    job: SuiteStart,
    *,
    allow_dirty: bool = False,
) -> SuiteResult | None:
    """If the background job finished, return a ``SuiteResult``; else ``None``."""
    if not suite_job_finished(job):
        return None
    if job.result_path is not None and not job.result_path.is_file():
        return _interrupted_result(job, allow_dirty=allow_dirty)
    return collect_suite(job, allow_dirty=allow_dirty)


def collect_suite(
    job: SuiteStart,
    *,
    allow_dirty: bool = False,
) -> SuiteResult:
    """Read the terminal result and log for a suite run."""
    if job.skipped:
        return SuiteResult(
            exit_code=SKIPPED_EXIT_CODE,
            duration_s=0.0,
            output="",
            output_sha256=output_sha256(""),
            failing_node_ids=[],
            result="skipped",
            revision=job.phase_head,
            skipped=True,
            skip_reason=job.skip_reason,
        )
    if job.result_path is None:
        raise RuntimeError("suite run metadata is missing its result path")
    if not job.result_path.is_file():
        if job.lifecycle_path is not None and not _lock_is_held(job.lifecycle_path):
            return _interrupted_result(job, allow_dirty=allow_dirty)
        raise RuntimeError("suite run is still active")
    terminal = read_suite_json_object(job.result_path)
    if terminal.get("run_id") != job.run_id:
        raise RuntimeError(f"invalid suite run metadata at {job.result_path}: run id mismatch")
    exit_code_value = terminal.get("exit_code")
    reason_value = terminal.get("reason")
    duration_value = terminal.get("duration_s")
    if not isinstance(reason_value, str) or not isinstance(duration_value, (int, float)):
        raise RuntimeError(
            f"invalid suite run metadata at {job.result_path}: missing result fields"
        )
    if exit_code_value is not None and not isinstance(exit_code_value, int):
        raise RuntimeError(f"invalid suite run metadata at {job.result_path}: invalid exit code")
    if not job.log_path.is_file():
        raise RuntimeError(f"required suite output is missing at {job.log_path}")
    output = job.log_path.read_text(encoding="utf-8", errors="replace")
    duration = float(duration_value)
    exit_code = exit_code_value if isinstance(exit_code_value, int) else 3
    result = map_process_outcome(exit_code=exit_code) if reason_value == "completed" else "blocked"
    if not suite_worktree_matches(job.worktree, job.start_head, job.start_diff_sha256):
        return _revision_changed_result(job, output, duration)
    revision, diff, refuse_msg = resolve_suite_revision(
        job.worktree,
        allow_dirty=allow_dirty,
        provisional_result=result,
    )
    if refuse_msg:
        return SuiteResult(
            exit_code=3,
            duration_s=round(duration, 6),
            output=output,
            output_sha256=output_sha256(output),
            failing_node_ids=parse_failing_node_ids(output),
            result="blocked",
            revision=revision,
            diff_sha256=diff,
            refuse=True,
            refuse_message=refuse_msg,
            run_id=job.run_id,
            reason=reason_value,
        )
    # Prefer the captured phase head when the tree stayed clean at that SHA.
    if revision not in ("dirty",) and job.phase_head:
        revision = job.start_head
    nodes = parse_failing_node_ids(output) if result == "fail" else []
    return SuiteResult(
        exit_code=exit_code,
        duration_s=round(duration, 6),
        output=output,
        output_sha256=output_sha256(output),
        failing_node_ids=nodes,
        result=result,
        revision=revision,
        diff_sha256=diff,
        run_id=job.run_id,
        reason=reason_value,
        worktree=job.worktree,
        start_head=job.start_head,
        start_diff_sha256=job.start_diff_sha256,
    )


def build_suite_check_run_payload(
    *,
    phase_slug: str,
    effort: str,
    suite: SuiteResult,
    criterion_id: str | None = None,
) -> JsonObject:
    """Parent-only payload for the suite ``tuner:check-run``."""
    subject = suite_subject(phase_slug)
    payload: JsonObject = {
        "criterion_id": criterion_id or subject,
        "revision": suite.revision,
        "result": suite.result,
        "effort": effort,
        "method": METHOD,
        "signed_by": "",
        "evidence_kind": EVIDENCE_KIND,
        "runner": RUNNER,
        "duration_s": suite.duration_s,
        "output_sha256": suite.output_sha256,
        "exit_code": suite.exit_code,
    }
    if suite.diff_sha256:
        payload["diff_sha256"] = suite.diff_sha256
    if suite.failing_node_ids:
        payload["failing_node_ids"] = list(suite.failing_node_ids)
    return payload


def is_suite_check_run(run: Mapping[str, JsonValue], *, phase_slug: str | None = None) -> bool:
    evidence = str(run.get("evidence_kind") or "")
    if evidence != EVIDENCE_KIND:
        return False
    subject = str(run.get("subject") or "")
    criterion = str(run.get("criterion_id") or "")
    if phase_slug:
        expected = suite_subject(phase_slug)
        return subject == expected or criterion == expected
    return is_suite_subject(subject) or is_suite_subject(criterion)


def acceptance_passes_at_head(
    *,
    acceptance_id: str,
    check_runs: Sequence[Mapping[str, JsonValue]],
    phase_head: str,
) -> bool:
    """True when a runner check-run for this criterion passes at the phase head."""
    matching: list[Mapping[str, JsonValue]] = []
    for run in check_runs:
        if str(run.get("criterion_id") or "") != acceptance_id:
            continue
        if is_suite_check_run(run):
            continue
        if str(run.get("method") or "") == "review":
            continue
        if not _revision_matches(str(run.get("revision") or ""), phase_head):
            continue
        matching.append(run)
    if not matching:
        return False
    # Prefer last in list (callers should pass chronological order).
    latest = matching[-1]
    return str(latest.get("result") or "") == "pass"


def suite_pass_at_head(
    *,
    check_runs: Sequence[Mapping[str, JsonValue]],
    phase_head: str,
    phase_slug: str,
) -> bool:
    for run in check_runs:
        if not is_suite_check_run(run, phase_slug=phase_slug):
            continue
        if str(run.get("result") or "") != "pass":
            continue
        if _revision_matches(str(run.get("revision") or ""), phase_head):
            return True
    return False


def _payload_text(run: Record, key: str) -> str:
    value = run["payload"].get(key)
    return value if isinstance(value, str) else ""


def suite_ready_for_review(
    policy: SuitePolicy,
    check_runs: Sequence[Record],
    *,
    phase_slug: str,
    phase_head: str,
) -> str:
    """Return why the reviewer may not start yet, or an empty string."""
    if not policy.run_locally:
        return ""
    subject = suite_subject(phase_slug)
    at_head = [
        run
        for run in check_runs
        if _payload_text(run, "evidence_kind") == EVIDENCE_KIND
        and subject in {run["subject"], _payload_text(run, "criterion_id")}
        and _revision_matches(_payload_text(run, "revision"), phase_head)
    ]
    if not at_head:
        return f"no {subject} check-run at {phase_head}"
    if policy.blocks_merge and not any(_payload_text(run, "result") == "pass" for run in at_head):
        return f"{subject} check-run at {phase_head} did not pass"
    return ""


def phase_suite_gate_holds(
    *,
    acceptances: Sequence[Mapping[str, JsonValue]],
    check_runs: Sequence[Mapping[str, JsonValue]],
    phase_head: str,
    phase_slug: str,
    policy: SuitePolicy | None = None,
) -> bool:
    """Merge gate: every active acceptance pass@head, plus suite when required.

    When policy gate is advisory/deferred or mode is none, missing/failing
    suite does not block. Required mode with a runnable or external suite
    still needs a passing ``<phase>-suite`` check-run at head.
    """
    for acc in acceptances:
        state = str(acc.get("lifecycle_state") or "active")
        if state in ("withdrawn", "superseded"):
            continue
        acc_id = str(acc.get("id") or acc.get("criterion_id") or "")
        if not acc_id:
            continue
        if not acceptance_passes_at_head(
            acceptance_id=acc_id,
            check_runs=check_runs,
            phase_head=phase_head,
        ):
            return False
    resolved = policy
    if resolved is None:
        resolved = SuitePolicy(mode="full", command="x", gate="required")
    if not resolved.blocks_merge:
        return True
    return suite_pass_at_head(
        check_runs=check_runs,
        phase_head=phase_head,
        phase_slug=phase_slug,
    )


def record_suite_check_run(
    *,
    store_root: Path,
    store_dir: Path | None = None,
    phase_slug: str,
    effort: str,
    suite: SuiteResult,
    criterion_id: str | None = None,
) -> Record:
    """Create the suite check-run via canon (parent session only)."""
    if suite.refuse:
        raise RuntimeError(suite.refuse_message or "refusing suite check-run")
    if suite.skipped:
        raise RuntimeError(suite.skip_reason or "suite was skipped; no check-run")
    if (
        suite.result == "pass"
        and suite.worktree is not None
        and not suite_worktree_matches(
            suite.worktree,
            suite.start_head,
            suite.start_diff_sha256,
        )
    ):
        raise RuntimeError("suite worktree changed after collection; refusing passing check-run")
    subject = suite_subject(phase_slug)
    payload = build_suite_check_run_payload(
        phase_slug=phase_slug,
        effort=effort,
        suite=suite,
        criterion_id=criterion_id,
    )
    body_parts = [_body_tail(suite.output)]
    if suite.failing_node_ids:
        body_parts.append(
            "\n## Failing node IDs\n\n" + "\n".join(f"- {n}" for n in suite.failing_node_ids)
        )
    try:
        project = open_store(store_root, store=store_dir)
        return project.create(
            record_type="tuner:check-run",
            subject=subject,
            payload=payload,
            body="\n".join(body_parts),
        )
    except (StoreBindingError, StoreError, ValidationError) as exc:
        raise RuntimeError(str(exc)) from exc


def orphan_recovery_hint(job: SuiteStart) -> str:
    """Point to persistent diagnostics for an orphaned suite run."""
    worker_log = job.run_dir / "worker.log" if job.run_dir else job.log_path
    result = job.result_path if job.result_path else job.exit_path
    return f"Orphaned suite run {job.run_id}: inspect `{worker_log}` and `{result}`."
