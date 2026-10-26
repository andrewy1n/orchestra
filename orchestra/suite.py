"""Phase-level suite runner: policy, background tmux, check-run, gate, fix routing.

Parent session loads ``phase_gate.suite`` from the store config, starts the
configured command in a detached tmux window in the phase worktree when mode
is smoke/full, polls for completion, and records one ``aff:check-run`` with
``evidence_kind: integration`` and subject ``<phase>-suite``. Does not
fix-and-rerun inline. Suite is never red-first.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from canon.project import StoreBindingError, open_store
from canon.store import StoreError
from canon.validation import ValidationError
from orchestra.check import (
    OUTPUT_BODY_CHARS,
    RUNNER,
    git_diff_sha256,
    git_head,
    git_is_dirty,
)
from orchestra.policy import dirty_pass_decision, map_process_outcome
from orchestra.reviewer import _revision_matches

EVIDENCE_KIND = "integration"
SUBJECT_SUFFIX = "-suite"
LEGACY_SUBJECT_SUFFIX = "-tier2"
METHOD = "check"

SUITE_MODES = ("none", "smoke", "full", "external")
SUITE_GATES = ("required", "advisory", "deferred")

# Consumer / missing-design default: skip. When mode!=none and command set,
# omitted gate means required.
DEFAULT_SUITE_POLICY = {"mode": "none", "command": "", "gate": "required"}

# Fallback when policy command is empty but mode is smoke/full (legacy README).
FAST_SUITE_CMD = (
    'uv run --with textual --with pytest --with pytest-xdist '
    'python -m pytest tests -q -n 4 -m "not tmux"'
)
TMUX_SUITE_CMD = (
    "uv run --with textual --with pytest "
    "python -m pytest tests -q -m tmux"
)

_NODE_ID_RE = re.compile(
    r"(?:FAILED|ERROR)\s+(\S+::\S+)"
)
_SUMMARY_NODE_RE = re.compile(
    r"^(?:FAILED|ERROR)\s+(\S+::\S+)",
    re.MULTILINE,
)


@dataclass(frozen=True)
class SuitePolicy:
    """Configured ``phase_gate.suite`` after consumer defaults are applied."""

    mode: str = "none"
    command: str = ""
    gate: str = "required"
    source_path: str | None = None

    @property
    def run_locally(self) -> bool:
        """True when execute-phase should start the suite in the worktree."""
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


def normalize_suite_policy(
    raw: Mapping[str, Any] | None,
    *,
    source_path: str | None = None,
) -> SuitePolicy:
    """Apply consumer defaults to a raw ``phase_gate.suite`` object.

    Missing / empty → mode=none (skip). When mode!=none and command is set,
    omitted gate defaults to required.
    """
    if not raw:
        return SuitePolicy(
            mode=DEFAULT_SUITE_POLICY["mode"],
            command=DEFAULT_SUITE_POLICY["command"],
            gate=DEFAULT_SUITE_POLICY["gate"],
            source_path=source_path,
        )
    mode = str(raw.get("mode") or "none").strip() or "none"
    command = str(raw.get("command") or "")
    if "gate" in raw and raw.get("gate") not in (None, ""):
        gate = str(raw.get("gate")).strip()
    elif mode != "none" and command.strip():
        gate = "required"
    else:
        gate = DEFAULT_SUITE_POLICY["gate"]
    if mode not in SUITE_MODES:
        mode = "none"
    if gate not in SUITE_GATES:
        gate = "required"
    return SuitePolicy(
        mode=mode,
        command=command,
        gate=gate,
        source_path=source_path,
    )


def load_suite_policy(start: Path | None = None) -> SuitePolicy:
    """Load ``phase_gate.suite`` from ``config.json`` under ``settings.run``.

    A missing store, key, or malformed value yields the consumer default
    (mode=none, skip). Agents must not waive or override this policy; change
    the store config instead.
    """
    root = start or Path.cwd()
    try:
        config_path = open_store(root).store_path / "config.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (StoreBindingError, OSError, ValueError, TypeError):
        return normalize_suite_policy(None)
    settings = data.get("settings") if isinstance(data, dict) else None
    run = settings.get("run") if isinstance(settings, dict) else None
    phase_gate = run.get("phase_gate") if isinstance(run, dict) else None
    suite_raw = phase_gate.get("suite") if isinstance(phase_gate, dict) else None
    if not isinstance(suite_raw, dict):
        return normalize_suite_policy(None)
    return normalize_suite_policy(suite_raw, source_path=str(config_path))


def suite_subject(phase_slug: str) -> str:
    slug = (phase_slug or "").strip()
    if not slug:
        raise ValueError("phase_slug is required")
    if slug.endswith(SUBJECT_SUFFIX):
        return slug
    if slug.endswith(LEGACY_SUBJECT_SUFFIX):
        return slug[: -len(LEGACY_SUBJECT_SUFFIX)] + SUBJECT_SUFFIX
    return f"{slug}{SUBJECT_SUFFIX}"


def is_suite_subject(subject: str) -> bool:
    text = (subject or "").strip()
    return text.endswith(SUBJECT_SUFFIX) or text.endswith(LEGACY_SUBJECT_SUFFIX)


def readme_suite_command() -> str:
    """Command chain matching README Testing full suite (fast then tmux)."""
    return f"{FAST_SUITE_CMD} && {TMUX_SUITE_CMD}"


def suite_command_for_policy(policy: SuitePolicy) -> str:
    """Command to run for a smoke/full policy; empty when not run locally."""
    if not policy.run_locally:
        return ""
    return policy.command.strip() or readme_suite_command()


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
    suite: "SuiteResult",
) -> dict[str, Any]:
    """Finding payload for an advisory suite fail (does not block merge)."""
    subject = suite_subject(phase_slug)
    nodes = ", ".join(suite.failing_node_ids[:8]) if suite.failing_node_ids else "(see check-run)"
    return {
        "claim": f"advisory suite fail for {subject} at {suite.revision}",
        "basis": f"exit_code={suite.exit_code}; failing: {nodes}",
        "invalidated_when": (
            "suite check-run passes at phase head, or human clears the finding"
        ),
        "effort": effort,
        "needs": "none",
    }


def _output_sha256(output: str) -> str:
    return hashlib.sha256(output.encode("utf-8", "replace")).hexdigest()


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


@dataclass
class SuiteResult:
    exit_code: int
    duration_s: float
    output: str
    output_sha256: str
    failing_node_ids: list[str]
    result: str  # pass | fail | blocked
    revision: str
    diff_sha256: str | None = None
    refuse: bool = False
    refuse_message: str = ""
    skipped: bool = False
    skip_reason: str = ""


def resolve_suite_revision(
    cwd: Path,
    *,
    allow_dirty: bool = False,
    provisional_result: str = "pass",
) -> tuple[str, str | None, str | None]:
    """Return (revision, diff_sha256|None, refuse_message|None).

    Dirty pass is refused without ``allow_dirty``, matching check dirty policy.
    """
    head = git_head(cwd)
    dirty = git_is_dirty(cwd)
    diff = git_diff_sha256(cwd) if dirty else None
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
    tmux: str = "tmux",
    runner: Any = None,
) -> SuiteStart | SuiteResult:
    """Start the suite in a detached tmux session; return immediately.

    When policy says not to run locally (mode=none/external, gate=deferred),
    returns a ``SuiteStart`` with ``skipped=True`` and does not start tmux.
    On dirty-pass refusal, returns a ``SuiteResult`` with ``refuse=True``.
    """
    work = worktree.resolve()
    resolved_policy = policy if policy is not None else load_suite_policy(work)
    head = phase_head or git_head(work)

    if not resolved_policy.run_locally and suite_command is None:
        reason = (
            f"suite skipped (mode={resolved_policy.mode}, gate={resolved_policy.gate})"
        )
        return SuiteStart(
            session_name=session_name or f"orchestra-suite-{phase_slug.strip()}",
            worktree=work,
            phase_slug=phase_slug.strip(),
            phase_head=head,
            log_path=work / ".suite" / "skipped.log",
            exit_path=work / ".suite" / "skipped.exit",
            started_monotonic=time.monotonic(),
            blocking=False,
            skipped=True,
            skip_reason=reason,
            policy=resolved_policy,
        )

    revision, _diff, refuse_msg = resolve_suite_revision(
        work, allow_dirty=allow_dirty, provisional_result="pass",
    )
    if refuse_msg:
        return SuiteResult(
            exit_code=3,
            duration_s=0.0,
            output="",
            output_sha256=_output_sha256(""),
            failing_node_ids=[],
            result="blocked",
            revision=revision,
            refuse=True,
            refuse_message=refuse_msg,
        )

    slug = phase_slug.strip()
    name = session_name or f"orchestra-suite-{slug}"
    out_dir = (log_dir or (work / ".suite")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / f"{name}.log"
    exit_path = out_dir / f"{name}.exit"
    for path in (log_path, exit_path):
        if path.exists():
            path.unlink()

    if suite_command is not None:
        cmd = suite_command
    else:
        cmd = suite_command_for_policy(resolved_policy)
    # Record exit code after the chain; keep full stdout/stderr in the log.
    inner = (
        f"cd {shlex.quote(str(work))} && "
        f"({{ {cmd}; }}; ec=$?; echo $ec > {shlex.quote(str(exit_path))}; "
        f"exit $ec) >{shlex.quote(str(log_path))} 2>&1"
    )
    tmux_args = [
        tmux,
        "new-session",
        "-d",
        "-s",
        name,
        "-c",
        str(work),
        f"bash -lc {shlex.quote(inner)}",
    ]
    run = runner or subprocess.run
    run(tmux_args, check=False, capture_output=True, text=True)
    return SuiteStart(
        session_name=name,
        worktree=work,
        phase_slug=slug,
        phase_head=head,
        log_path=log_path,
        exit_path=exit_path,
        started_monotonic=time.monotonic(),
        blocking=False,
        policy=resolved_policy,
    )


def suite_job_finished(job: SuiteStart) -> bool:
    if job.skipped:
        return True
    return job.exit_path.is_file()


def poll_suite(
    job: SuiteStart,
    *,
    allow_dirty: bool = False,
) -> SuiteResult | None:
    """If the background job finished, return a ``SuiteResult``; else ``None``."""
    if job.skipped:
        return SuiteResult(
            exit_code=0,
            duration_s=0.0,
            output="",
            output_sha256=_output_sha256(""),
            failing_node_ids=[],
            result="pass",
            revision=job.phase_head,
            skipped=True,
            skip_reason=job.skip_reason,
        )
    if not suite_job_finished(job):
        return None
    return collect_suite(job, allow_dirty=allow_dirty)


def collect_suite(
    job: SuiteStart,
    *,
    allow_dirty: bool = False,
) -> SuiteResult:
    """Read exit code / log for a finished (or finishing) job."""
    if job.skipped:
        return SuiteResult(
            exit_code=0,
            duration_s=0.0,
            output="",
            output_sha256=_output_sha256(""),
            failing_node_ids=[],
            result="pass",
            revision=job.phase_head,
            skipped=True,
            skip_reason=job.skip_reason,
        )
    output = ""
    if job.log_path.is_file():
        output = job.log_path.read_text(encoding="utf-8", errors="replace")
    exit_code = 1
    if job.exit_path.is_file():
        raw = job.exit_path.read_text(encoding="utf-8", errors="replace").strip()
        try:
            exit_code = int(raw.splitlines()[-1])
        except (ValueError, IndexError):
            exit_code = 1
    duration = max(0.0, time.monotonic() - job.started_monotonic)
    result = map_process_outcome(exit_code=exit_code)
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
            output_sha256=_output_sha256(output),
            failing_node_ids=parse_failing_node_ids(output),
            result="blocked",
            revision=revision,
            diff_sha256=diff,
            refuse=True,
            refuse_message=refuse_msg,
        )
    # Prefer the captured phase head when the tree stayed clean at that SHA.
    if revision not in ("dirty",) and job.phase_head:
        revision = job.phase_head
    nodes = parse_failing_node_ids(output) if result == "fail" else []
    return SuiteResult(
        exit_code=exit_code,
        duration_s=round(duration, 6),
        output=output,
        output_sha256=_output_sha256(output),
        failing_node_ids=nodes,
        result=result,
        revision=revision,
        diff_sha256=diff,
    )


def build_suite_check_run_payload(
    *,
    phase_slug: str,
    effort: str,
    suite: SuiteResult,
    criterion_id: str | None = None,
) -> dict[str, Any]:
    """Parent-only payload for the suite ``aff:check-run``."""
    subject = suite_subject(phase_slug)
    payload: dict[str, Any] = {
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


def is_suite_check_run(run: Mapping[str, Any], *, phase_slug: str | None = None) -> bool:
    evidence = str(run.get("evidence_kind") or "")
    if evidence != EVIDENCE_KIND:
        return False
    subject = str(run.get("subject") or "")
    criterion = str(run.get("criterion_id") or "")
    if phase_slug:
        expected = suite_subject(phase_slug)
        legacy = f"{phase_slug.strip()}{LEGACY_SUBJECT_SUFFIX}"
        return (
            subject in (expected, legacy)
            or criterion in (expected, legacy)
            or is_suite_subject(subject)
        )
    return is_suite_subject(subject) or is_suite_subject(criterion)


def acceptance_passes_at_head(
    *,
    acceptance_id: str,
    check_runs: Sequence[Mapping[str, Any]],
    phase_head: str,
) -> bool:
    """True when a runner check-run for this criterion passes at the phase head."""
    matching: list[Mapping[str, Any]] = []
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
    check_runs: Sequence[Mapping[str, Any]],
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


def phase_suite_gate_holds(
    *,
    acceptances: Sequence[Mapping[str, Any]],
    check_runs: Sequence[Mapping[str, Any]],
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
    if not suite_pass_at_head(
        check_runs=check_runs,
        phase_head=phase_head,
        phase_slug=phase_slug,
    ):
        return False
    return True


def record_suite_check_run(
    *,
    store_root: Path,
    phase_slug: str,
    effort: str,
    suite: SuiteResult,
    criterion_id: str | None = None,
) -> dict[str, Any]:
    """Create the suite check-run via canon (parent session only)."""
    if suite.refuse:
        raise RuntimeError(suite.refuse_message or "refusing suite check-run")
    if suite.skipped:
        raise RuntimeError(suite.skip_reason or "suite was skipped; no check-run")
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
            "\n## Failing node IDs\n\n"
            + "\n".join(f"- {n}" for n in suite.failing_node_ids)
        )
    try:
        project = open_store(store_root)
        return project.create(
            record_type="aff:check-run",
            subject=subject,
            payload=payload,
            body="\n".join(body_parts),
        )
    except (StoreBindingError, StoreError, ValidationError) as exc:
        raise RuntimeError(str(exc)) from exc


def orphan_recovery_hint(job: SuiteStart) -> str:
    """Document how to recover if the tmux job is orphaned."""
    return (
        f"Orphaned suite: reattach with `tmux attach -t {job.session_name}` "
        f"or inspect `{job.log_path}` / `{job.exit_path}`; "
        f"re-run start_suite_background in the phase worktree if the session is gone."
    )
