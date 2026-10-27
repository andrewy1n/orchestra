"""Build a phase-end reviewer brief with restricted inputs (no builder self-grades).

Also parse reviewer output and build parent-side check-run / finding / gate /
integration-report payloads. The reviewer process never writes store records;
these helpers are for the parent session only.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

# Kinds the reviewer must never see (builder self-grades / dispatch notes).
EXCLUDED_KINDS = frozenset(
    {
        "execution-report",
        "check-run",
        "assessment",
        "assignment",
        "assignment-amendment",
    }
)

# Store-derived text the brief may include.
ALLOWED_KINDS = frozenset(
    {
        "work-item",
        "acceptance",
        "requirement",
        "specification",
        "design",
    }
)

# NEEDS_WORK finding kinds that may become retry-loop fix tasks.
FIXABLE_FINDING_KINDS = frozenset(
    {
        "spec-gap",
        "behavior-bug",
        "missing-test",
        "invariant-violation",
    }
)


def _short_kind(record_type: str) -> str:
    name = (record_type or "").strip()
    if ":" in name:
        name = name.split(":", 1)[1]
    return name


def is_excluded_kind(record_type: str) -> bool:
    return _short_kind(record_type) in EXCLUDED_KINDS


def filter_reviewer_records(
    records: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Drop excluded kinds; keep only allowed task/spec text."""
    kept: list[Mapping[str, Any]] = []
    for record in records:
        kind = _short_kind(str(record.get("record_type") or record.get("kind") or ""))
        if kind in EXCLUDED_KINDS:
            continue
        if kind and kind not in ALLOWED_KINDS:
            continue
        kept.append(record)
    return kept


def phase_diff_range(base: str, phase_head: str) -> str:
    return f"{base}..{phase_head}"


def git_phase_diff(
    cwd: Path,
    *,
    base: str = "main",
    phase_head: str = "HEAD",
) -> str:
    """Return `git diff <base>..<phase-head>` text (empty string on failure)."""
    result = subprocess.run(
        ["git", "-C", str(cwd), "diff", f"{base}..{phase_head}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout or ""


def _record_text(record: Mapping[str, Any]) -> str:
    parts: list[str] = []
    title = record.get("title") or record.get("subject") or ""
    subject = record.get("subject") or ""
    if title:
        parts.append(f"**{title}**" + (f" (`{subject}`)" if subject and subject != title else ""))
    criterion = record.get("criterion")
    if criterion:
        parts.append(f"**criterion**: {criterion}")
    body = record.get("body") or record.get("text") or ""
    if body:
        parts.append(str(body).rstrip())
    return "\n\n".join(parts)


def build_reviewer_brief(
    *,
    records: Sequence[Mapping[str, Any]],
    phase_diff: str,
    base: str = "main",
    phase_head: str = "HEAD",
) -> str:
    """Compose the reviewer brief from allowed records plus the phase diff.

    Strips execution-report, check-run, assessment, and assignment content
    even if present in ``records``.
    """
    allowed = filter_reviewer_records(records)
    sections: list[str] = [
        "# Reviewer brief",
        "",
        "Inputs are limited to work-item descriptions/Approach goals, "
        "acceptances, requirements/invariants, and the phase diff. "
        "Execution reports, check-runs, assessments, and assignment notes "
        "are excluded.",
        "",
    ]

    by_kind: dict[str, list[Mapping[str, Any]]] = {}
    for record in allowed:
        kind = _short_kind(str(record.get("record_type") or record.get("kind") or "work-item"))
        by_kind.setdefault(kind, []).append(record)

    heading = {
        "work-item": "Work items",
        "acceptance": "Acceptance criteria",
        "requirement": "Requirements",
        "specification": "Specification",
        "design": "Design / invariants",
    }
    for kind in ("work-item", "acceptance", "requirement", "specification", "design"):
        items = by_kind.get(kind) or []
        if not items:
            continue
        sections.append(f"## {heading[kind]}")
        sections.append("")
        for item in items:
            text = _record_text(item)
            if text:
                sections.append(text)
                sections.append("")

    diff_label = phase_diff_range(base, phase_head)
    sections.append("## Phase diff")
    sections.append("")
    sections.append(f"`git diff {diff_label}`")
    sections.append("")
    sections.append("```diff")
    sections.append(phase_diff.rstrip() if phase_diff else "(empty)")
    sections.append("```")
    sections.append("")

    return "\n".join(sections)


def _strip_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def parse_reviewer_output(text: str) -> dict[str, Any]:
    """Parse the structured PASS/NEEDS_WORK block from the reviewer."""
    raw = _strip_fence(text)
    verdict_m = re.search(r"(?im)^\s*verdict:\s*(\S+)", raw)
    verdict = (verdict_m.group(1) if verdict_m else "").strip().upper()
    if verdict in {"NEEDS_WORK", "NEEDS-WORK"}:
        verdict = "NEEDS_WORK"

    findings: list[dict[str, str]] = []
    findings_m = re.search(
        r"(?is)^\s*findings:\s*(.*?)^\s*integration:\s*",
        raw,
        re.MULTILINE,
    )
    findings_block = findings_m.group(1) if findings_m else ""
    if findings_block.strip() and findings_block.strip() not in {"[]", "-", "[]\n"}:
        chunks = re.split(r"(?m)^\s*-\s+task:\s*", findings_block)
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            task_line, _, rest = chunk.partition("\n")
            task = task_line.strip()
            kind_m = re.search(r"(?im)^\s*kind:\s*(\S+)", rest)
            expected_m = re.search(r"(?im)^\s*expected:\s*(.+)$", rest)
            observed_m = re.search(r"(?im)^\s*observed:\s*(.+)$", rest)
            severity_m = re.search(r"(?im)^\s*severity:\s*(\S+)", rest)
            findings.append(
                {
                    "task": task,
                    "kind": (kind_m.group(1) if kind_m else "").strip(),
                    "expected": (expected_m.group(1) if expected_m else "").strip(),
                    "observed": (observed_m.group(1) if observed_m else "").strip(),
                    "severity": (severity_m.group(1) if severity_m else "").strip(),
                }
            )

    integration: dict[str, str] = {
        "interfaces": "",
        "assumptions": "",
        "invariants": "",
        "conflicts": "",
    }
    integ_m = re.search(r"(?im)^\s*integration:\s*\n(.*)\Z", raw, re.DOTALL)
    if integ_m:
        block = integ_m.group(1)
        for key in ("interfaces", "assumptions", "invariants", "conflicts"):
            km = re.search(rf"(?im)^\s*{key}:\s*(.*)$", block)
            if km:
                integration[key] = km.group(1).strip()

    return {"verdict": verdict, "findings": findings, "integration": integration}


def verdict_to_result(verdict: str) -> str:
    normalized = (verdict or "").strip().upper().replace("-", "_")
    if normalized == "PASS":
        return "pass"
    return "fail"


def build_review_check_run_payload(
    *,
    criterion_id: str,
    phase_head: str,
    effort: str,
    verdict: str,
) -> dict[str, str]:
    """Parent-only payload for the phase-end review check-run."""
    return {
        "criterion_id": criterion_id,
        "revision": phase_head,
        "result": verdict_to_result(verdict),
        "effort": effort,
        "method": "review",
        "signed_by": "",
        "evidence_kind": "review",
    }


def is_fixable_finding_kind(kind: str) -> bool:
    return (kind or "").strip() in FIXABLE_FINDING_KINDS


def build_finding_payload(
    finding: Mapping[str, Any],
    *,
    effort: str,
    fix_task_created: bool,
) -> dict[str, str]:
    """Parent-only finding payload for one NEEDS_WORK item."""
    severity = str(finding.get("severity") or "").strip().lower()
    if severity == "judgment":
        needs = "human"
    elif fix_task_created:
        needs = "none"
    else:
        needs = "human"
    kind = str(finding.get("kind") or "finding")
    task = str(finding.get("task") or "phase")
    claim = f"{kind} on {task}: {finding.get('expected') or ''}".strip()
    basis = str(finding.get("observed") or "")
    return {
        "claim": claim,
        "basis": basis,
        "invalidated_when": "fix lands and reviewer re-run passes, or human clears",
        "effort": effort,
        "needs": needs,
    }


@dataclass
class ReviewRouting:
    create_fix_flags: list[bool] = field(default_factory=list)
    fix_subjects: list[str] = field(default_factory=list)
    escalate: bool = False
    reopen_done: bool = False


def route_review_findings(
    findings: Sequence[Mapping[str, Any]],
    *,
    fix_budget_remaining: int,
    reviewer_rerun_used: bool = False,
) -> ReviewRouting:
    """Decide which NEEDS_WORK items become fix tasks under the retry budget.

    Never reopens ``done`` work-items (``reopen_done`` is always False).
    Judgment severity does not create a fix task. Budget exhaustion escalates.
    """
    del reviewer_rerun_used  # reserved for callers; routing is budget-driven
    flags: list[bool] = []
    subjects: list[str] = []
    remaining = max(0, int(fix_budget_remaining))
    wanted_fixable = 0
    for finding in findings:
        kind = str(finding.get("kind") or "")
        severity = str(finding.get("severity") or "").strip().lower()
        task = str(finding.get("task") or "phase")
        fixable = is_fixable_finding_kind(kind) and severity != "judgment"
        if fixable:
            wanted_fixable += 1
        if fixable and remaining > 0:
            flags.append(True)
            subjects.append(f"fix-{task}-{kind}")
            remaining -= 1
        else:
            flags.append(False)
            subjects.append("")
    escalate = wanted_fixable > 0 and remaining == 0 and not any(flags)
    # Also escalate when some fixable items were skipped due to budget mid-batch.
    if wanted_fixable > sum(flags):
        escalate = True
    return ReviewRouting(
        create_fix_flags=flags,
        fix_subjects=subjects,
        escalate=escalate,
        reopen_done=False,
    )


def should_rerun_reviewer(*, fix_tasks_created: int, reviewer_rerun_used: bool) -> bool:
    """Re-run the reviewer once after fix tasks land; never a second re-run."""
    return bool(fix_tasks_created) and not reviewer_rerun_used


def _revision_matches(check_revision: str, phase_head: str) -> bool:
    a = (check_revision or "").strip().lower()
    b = (phase_head or "").strip().lower()
    if not a or not b:
        return False
    if a == b:
        return True
    # Allow abbreviated SHAs either direction.
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    return longer.startswith(shorter) and len(shorter) >= 7


def phase_review_gate_holds(
    *,
    check_runs: Sequence[Mapping[str, Any]],
    phase_head: str,
) -> bool:
    """True when a passing method:review check-run exists at the phase head."""
    for run in check_runs:
        method = str(run.get("method") or "")
        result = str(run.get("result") or "")
        revision = str(run.get("revision") or "")
        if method != "review":
            continue
        if result != "pass":
            continue
        if _revision_matches(revision, phase_head):
            return True
    return False


def integration_report_body(integration: Mapping[str, Any]) -> str:
    """Fill integration-report required sections from reviewer integration."""
    return (
        "## Interfaces\n\n"
        f"{integration.get('interfaces') or ''}\n\n"
        "## Assumptions\n\n"
        f"{integration.get('assumptions') or ''}\n\n"
        "## Invariants\n\n"
        f"{integration.get('invariants') or ''}\n\n"
        "## Conflicts\n\n"
        f"{integration.get('conflicts') or ''}"
    )


# UI labels used by the status-tabs dogfood / similar dashboard tab work.
_UI_LABELS = (
    "Active",
    "Done",
    "Archived",
    "Waiting",
    "Blocked",
    "Ready",
    "Needs you",
    "All",
)
_UI_LABEL_RE = re.compile(
    r"\b(" + "|".join(re.escape(label) for label in _UI_LABELS) + r")\b"
)


def _ui_labels_in(text: str) -> list[str]:
    """Return unique UI labels in first-seen order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for match in _UI_LABEL_RE.finditer(text or ""):
        label = match.group(1)
        if label not in seen:
            seen.add(label)
            ordered.append(label)
    return ordered


def grade_reviewer_inputs(
    *,
    records: Sequence[Mapping[str, Any]],
    phase_diff: str,
) -> dict[str, Any]:
    """Deterministic stub mirroring ``agents/se-reviewer.md`` spec-gap grading.

    When a work-item description promises UI labels that neither that task's
    acceptance criteria nor the phase diff cover, return NEEDS_WORK with a
    ``spec-gap`` finding. Builder self-grades in ``records`` are ignored.
    """
    allowed = filter_reviewer_records(records)
    accept_by_subject: dict[str, list[str]] = {}
    work_items: list[Mapping[str, Any]] = []
    for record in allowed:
        kind = _short_kind(str(record.get("record_type") or record.get("kind") or ""))
        subject = str(record.get("subject") or record.get("title") or "phase")
        if kind == "work-item":
            work_items.append(record)
        elif kind == "acceptance":
            text = " ".join(
                str(part)
                for part in (
                    record.get("criterion"),
                    record.get("body"),
                    record.get("text"),
                )
                if part
            )
            accept_by_subject.setdefault(subject, []).append(text)

    findings: list[dict[str, str]] = []
    delivered_global = _ui_labels_in(phase_diff or "")
    for item in work_items:
        subject = str(item.get("subject") or item.get("title") or "phase")
        description = " ".join(
            str(part)
            for part in (item.get("body"), item.get("text"), item.get("title"))
            if part
        )
        promised = _ui_labels_in(description)
        if not promised:
            continue
        accept_text = " ".join(accept_by_subject.get(subject, []))
        covered = set(_ui_labels_in(accept_text)) | set(delivered_global)
        missing = [label for label in promised if label not in covered]
        if not missing:
            continue
        findings.append(
            {
                "task": subject,
                "kind": "spec-gap",
                "expected": (
                    "Description lists "
                    + ", ".join(promised)
                    + " tabs/UI"
                ),
                "observed": (
                    "Acceptance and diff only cover "
                    + (", ".join(label for label in promised if label in covered) or "(none)")
                    + f"; missing: {', '.join(missing)}"
                ),
                "severity": "major",
            }
        )

    if findings:
        return {
            "verdict": "NEEDS_WORK",
            "findings": findings,
            "integration": {
                "interfaces": "spec-gap detected between description and acceptance/diff",
                "assumptions": "UI labels extracted from work-item description text",
                "invariants": "builder self-grades excluded from grading inputs",
                "conflicts": "; ".join(
                    f"{f['task']}: {f['observed']}" for f in findings
                ),
            },
        }
    return {
        "verdict": "PASS",
        "findings": [],
        "integration": {
            "interfaces": "description UI covered by acceptance/diff",
            "assumptions": "UI labels extracted from work-item description text",
            "invariants": "builder self-grades excluded from grading inputs",
            "conflicts": "",
        },
    }
