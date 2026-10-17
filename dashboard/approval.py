"""Needs-you detail evidence and confirm-modal helpers for human-gate approvals."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dashboard.artifact_store import Target, aa_command
from dashboard.dismiss import (
    ACTION_ACCEPT,
    ACTION_APPROVE,
    ACTION_REJECT,
    ACTION_SIGN,
    default_action,
    is_dismissible,
)
from dashboard.gates import PLAN_REVIEW_PREFIX, plan_review_slug
from dashboard.landing import rev_parse_token
from dashboard.model import EffortView, NeedsYouItem


NOTE_REQUIRED_ACTIONS = frozenset({ACTION_REJECT, ACTION_ACCEPT})


@dataclass(frozen=True)
class ConfirmChoice:
    action: str
    label: str
    note_required: bool


def confirm_choices(item: NeedsYouItem) -> list[ConfirmChoice]:
    """Primary confirm actions available for this Needs-you kind."""
    if not is_dismissible(item.kind):
        return []
    if item.kind in ("blocking-question", "open-question"):
        return [
            ConfirmChoice(ACTION_APPROVE, "Approve", False),
            ConfirmChoice(ACTION_REJECT, "Reject", True),
        ]
    if item.kind == "unsigned-check":
        return [ConfirmChoice(ACTION_SIGN, "Sign", False)]
    if item.kind == "needs-human":
        return [ConfirmChoice(ACTION_ACCEPT, "Accept risk", True)]
    return []


def note_required_for(action: str) -> bool:
    return action in NOTE_REQUIRED_ACTIONS


def action_label(action: str) -> str:
    return {
        ACTION_APPROVE: "Approve",
        ACTION_REJECT: "Reject",
        ACTION_SIGN: "Sign",
        ACTION_ACCEPT: "Accept risk",
    }.get(action, action)


def _payload(record: dict[str, Any]) -> dict[str, Any]:
    payload = record.get("payload")
    return payload if isinstance(payload, dict) else {}


def _section(body: str, heading: str) -> str:
    marker = f"## {heading}"
    lines = (body or "").splitlines()
    collecting = False
    collected: list[str] = []
    for line in lines:
        if line.strip() == marker:
            collecting = True
            continue
        if collecting and line.startswith("## "):
            break
        if collecting:
            collected.append(line)
    return "\n".join(collected).strip()


def _cli_json(target: Target, *args: str) -> dict[str, Any]:
    command = [*aa_command(), *target.cli_args(), *args]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if result.returncode != 0:
        return {}
    try:
        data = json.loads(result.stdout or "")
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    record = data.get("record")
    return record if isinstance(record, dict) else data


def _git_head(root: Path) -> str:
    sha = rev_parse_token(root, "HEAD")
    return (sha or "").strip()


def _short(sha: str, n: int = 7) -> str:
    value = (sha or "").strip()
    if value.startswith("sha256:"):
        return value
    return value[:n] if len(value) > n else value


def _revisions_match(checked: str, head: str) -> bool:
    if not checked or not head:
        return False
    if checked == head:
        return True
    return head.startswith(checked) or checked.startswith(head[: max(len(checked), 7)])


def _finding_evidence(item: NeedsYouItem, record: dict[str, Any]) -> list[tuple[str, str]]:
    payload = _payload(record) if record else {}
    claim = (payload.get("claim") or item.text or "").strip()
    basis = (payload.get("basis") or "").strip()
    body = (record.get("body") if record else None) or item.body or ""
    evidence = _section(body, "Evidence")
    consequence = _section(body, "Consequence")
    lines = [
        f"**Claim.** {claim}" if claim else "",
        f"**Basis.** {basis}" if basis else "",
        f"**Evidence.**\n\n{evidence}" if evidence else "",
        f"**Consequence.**\n\n{consequence}" if consequence else "",
    ]
    text = "\n\n".join(part for part in lines if part)
    return [("Finding", text)] if text else []


def _check_evidence(
    target: Target, item: NeedsYouItem, root: Path, record: dict[str, Any],
) -> list[tuple[str, str]]:
    payload = _payload(record) if record else {}
    check_body = ((record.get("body") if record else None) or item.body or "").strip()
    checked_rev = str(payload.get("revision") or "").strip()
    head = _git_head(root)
    acceptance_text = ""
    criterion_id = str(payload.get("criterion_id") or "").strip()
    if criterion_id:
        acceptance = _cli_json(target, "get", "--id", criterion_id, "--type", "project:acceptance")
        if acceptance:
            acceptance_text = str(_payload(acceptance).get("criterion") or "").strip()
            if acceptance.get("body"):
                acceptance_text = (
                    f"{acceptance_text}\n\n{(acceptance.get('body') or '').strip()}"
                ).strip()
    rev_line = (
        f"**Revision.** check `{_short(checked_rev)}` · HEAD `{_short(head) or 'unknown'}`"
    )
    if checked_rev and head and not checked_rev.startswith("sha256:"):
        rev_line += (
            " · matches HEAD" if _revisions_match(checked_rev, head) else " · **differs from HEAD**"
        )
    parts = [
        f"**Acceptance.** {acceptance_text}" if acceptance_text else "",
        rev_line,
        f"**Check body.**\n\n{check_body}" if check_body else "",
    ]
    text = "\n\n".join(part for part in parts if part)
    return [("Evidence", text)] if text else []


def _plan_review_evidence(item: NeedsYouItem, view: EffortView | None) -> list[tuple[str, str]]:
    slug = plan_review_slug(item)
    if slug is None or view is None:
        return []
    phase = next((row for row in view.phases if row.subject == slug), None)
    body = (phase.body if phase is not None else "") or ""
    tasks = [task for task in view.tasks if task.phase == slug and task.status != "withdrawn"]
    task_lines = "\n".join(
        f"- `{task.subject}` — {task.title} ({task.status}"
        + (f", wave {task.wave}" if task.wave is not None else "")
        + (f", {task.size}" if task.size else "")
        + (f", {task.estimate_minutes}m" if task.estimate_minutes is not None else "")
        + ")"
        for task in tasks
    )
    facts: list[str] = []
    if phase is not None:
        if phase.sitting:
            facts.append(f"Sitting: {phase.sitting}")
        if phase.elapsed_minutes is not None:
            facts.append(f"Elapsed estimate: {phase.elapsed_minutes}m")
        if phase.unset_estimates:
            facts.append(f"Unset estimates: {phase.unset_estimates}")
        facts.append(f"Tasks done: {phase.done}/{phase.total}")
    blocks = [
        body.strip(),
        f"## Tasks\n\n{task_lines}" if task_lines else "",
        ("## Run facts\n\n" + "\n".join(f"- {line}" for line in facts)) if facts else "",
    ]
    text = "\n\n".join(part for part in blocks if part)
    title = f"Phase {slug}"
    return [(title, text)] if text else [("Phase", f"No phase body for `{slug}`.")]


def evidence_panels(
    target: Target,
    item: NeedsYouItem,
    *,
    root: Path,
    view: EffortView | None,
) -> list[tuple[str, str]]:
    """Kind-specific evidence panels for the Needs-you detail screen."""
    if item.kind == "needs-human":
        record = _cli_json(target, "get", "--id", item.id, "--type", item.record_type or "project:finding")
        return _finding_evidence(item, record)
    if item.kind == "unsigned-check":
        record = _cli_json(
            target, "get", "--id", item.id, "--type", item.record_type or "project:check-run",
        )
        return _check_evidence(target, item, root, record)
    if item.kind in ("blocking-question", "open-question"):
        if item.text.startswith(PLAN_REVIEW_PREFIX) or plan_review_slug(item) is not None:
            return _plan_review_evidence(item, view)
        return []
    return []


# Re-export for callers that want the dismiss default.
primary_action = default_action
