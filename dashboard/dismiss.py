"""Dismiss human Needs-you items via the adaptive-artifacts CLI.

Human-gate clears always pass the displayed record revision as
``--expected-revision`` (never ``@current``). ``correct`` has no
expected-revision flag, so sign-off guards the revision with a ``get``
before writing.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any

from dashboard.artifact_store import Target, aa_command
from dashboard.model import NeedsYouItem

HUMAN_DISMISSIBLE = frozenset({
    "blocking-question", "open-question", "needs-human", "unsigned-check",
})

DEFAULT_SIGNER_ENV = "SE_WORKFLOW_SIGNED_BY"

# Actions for dismiss_command / dismiss_item.
ACTION_APPROVE = "approve"
ACTION_REJECT = "reject"
ACTION_SIGN = "sign"
ACTION_ACCEPT = "accept"

# ``correct`` does not accept --expected-revision; guard via get instead.
CORRECT_SUPPORTS_EXPECTED_REVISION = False

STALE_MESSAGE = "Item changed since opened (stale revision); refresh and try again."


class DismissError(Exception):
    """CLI or validation failure while dismissing."""


class DismissRefused(DismissError):
    """Item kind is not human-dismissible from the dashboard."""


@dataclass(frozen=True)
class DismissResult:
    ok: bool
    message: str = ""


def is_dismissible(kind: str) -> bool:
    return kind in HUMAN_DISMISSIBLE


def default_signer() -> str:
    return (
        os.environ.get(DEFAULT_SIGNER_ENV)
        or os.environ.get("USER")
        or os.environ.get("USERNAME")
        or "dashboard"
    )


def _cli(target: Target, *args: str) -> subprocess.CompletedProcess[str]:
    command = [*aa_command(), *target.cli_args(), *args]
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DismissError(f"cannot run {command[0]}: {exc}") from exc


def _parse_json(stdout: str) -> dict[str, Any]:
    try:
        data = json.loads(stdout or "")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _is_stale_result(result: subprocess.CompletedProcess[str]) -> bool:
    payload = _parse_json(result.stdout or "")
    if payload.get("error") == "stale_write":
        return True
    detail = f"{result.stdout or ''}{result.stderr or ''}".lower()
    return "stale write" in detail or "stale_write" in detail


def _fail(result: subprocess.CompletedProcess[str], label: str) -> None:
    if _is_stale_result(result):
        raise DismissError(STALE_MESSAGE)
    detail = (result.stdout or result.stderr or "").strip() or f"exit {result.returncode}"
    raise DismissError(f"{label} failed: {detail.splitlines()[0]}")


def _displayed_revision(item: NeedsYouItem) -> str:
    revision = (item.revision or "").strip()
    if not revision or revision == "@current":
        raise DismissError(
            "missing displayed revision; human-gate clears require the record "
            "revision as shown (never @current)"
        )
    return revision


def default_action(kind: str) -> str:
    """Primary confirm action for a human-dismissible Needs-you kind."""
    if kind in ("blocking-question", "open-question"):
        return ACTION_APPROVE
    if kind == "needs-human":
        return ACTION_ACCEPT
    return ACTION_SIGN


def _resolve_action(item: NeedsYouItem, action: str | None) -> str:
    resolved = (action or default_action(item.kind)).strip().lower()
    if item.kind in ("blocking-question", "open-question"):
        if resolved not in (ACTION_APPROVE, ACTION_REJECT):
            raise DismissError(f"unsupported action {resolved!r} for {item.kind}")
    elif item.kind == "needs-human":
        if resolved != ACTION_ACCEPT:
            raise DismissError(f"unsupported action {resolved!r} for {item.kind}")
    elif item.kind == "unsigned-check":
        if resolved != ACTION_SIGN:
            raise DismissError(f"unsupported action {resolved!r} for {item.kind}")
    return resolved


def _question_approve_args(item: NeedsYouItem, note: str | None) -> list[str]:
    record_type = item.record_type or "project:continuity-question"
    args = [
        "update", "--type", record_type, "--id", item.id,
        "--transition", "answered", "--expected-revision", _displayed_revision(item),
    ]
    if note:
        args.extend(["--payload", json.dumps({"answer": note})])
    return args


def _question_reject_args(item: NeedsYouItem, note: str | None) -> list[str]:
    """Leave the continuity-question open; create a needs:human routing finding."""
    _displayed_revision(item)  # require displayed revision even though create has none
    scope = item.text or item.subject
    rationale = (note or "").strip() or "Rejected from dashboard Needs-you"
    claim = f"Plan rejected for {scope}; route to discuss or plan-phase"
    payload = {
        "claim": claim,
        "basis": rationale,
        "needs": "human",
        "effort": item.subject,
        "invalidated_when": "approach re-discussed or plan-phase re-run",
    }
    body = (
        "## Evidence\n\n"
        f"Plan review rejected from the dashboard for {scope}.\n\n"
        "## Consequence\n\n"
        "Continuity-question remains open; engage should route to discuss or plan-phase.\n\n"
        "## Follow-up\n\n"
        f"{rationale}"
    )
    subject = f"plan-rejected:{scope}"[:120]
    return [
        "create", "--type", "project:finding", "--subject", subject,
        "--payload", json.dumps(payload), "--body", body,
    ]


def _finding_accept_args(item: NeedsYouItem, note: str | None) -> list[str]:
    record_type = item.record_type or "project:finding"
    payload: dict[str, str] = {"needs": "none"}
    if note:
        payload["resolution_note"] = note
    return [
        "update", "--type", record_type, "--id", item.id,
        "--expected-revision", _displayed_revision(item),
        "--payload", json.dumps(payload),
    ]


def _check_sign_args(item: NeedsYouItem, signer: str, note: str | None) -> list[str]:
    # correct has no --expected-revision; revision is guarded in dismiss_item.
    record_type = item.record_type or "project:check-run"
    _displayed_revision(item)
    payload: dict[str, str] = {"signed_by": signer}
    if note:
        payload["signed_note"] = note
    return [
        "correct", "--type", record_type, "--id", item.id,
        "--payload", json.dumps(payload),
    ]


def dismiss_command(
    item: NeedsYouItem,
    *,
    signer: str | None = None,
    action: str | None = None,
    note: str | None = None,
) -> list[str]:
    """Return the adaptive-artifacts argv (after root/store/contract) for this item.

    Never emits ``--expected-revision @current``. Approve/accept/sign include
    note fields when ``note`` is provided. Reject returns a ``create`` finding
    argv and does not answer the continuity-question.
    """
    if not is_dismissible(item.kind):
        raise DismissRefused(f"cannot dismiss {item.kind}")
    resolved = _resolve_action(item, action)
    if resolved == ACTION_APPROVE:
        return _question_approve_args(item, note)
    if resolved == ACTION_REJECT:
        return _question_reject_args(item, note)
    if resolved == ACTION_ACCEPT:
        return _finding_accept_args(item, note)
    return _check_sign_args(item, signer or default_signer(), note)


def _current_revision(target: Target, item: NeedsYouItem) -> str:
    record_type = item.record_type or {
        "blocking-question": "project:continuity-question",
        "open-question": "project:continuity-question",
        "needs-human": "project:finding",
        "unsigned-check": "project:check-run",
    }.get(item.kind, "")
    args = ["get", "--id", item.id]
    if record_type:
        args.extend(["--type", record_type])
    result = _cli(target, *args)
    if result.returncode != 0:
        _fail(result, "get")
    payload = _parse_json(result.stdout or "")
    record = payload.get("record") if isinstance(payload.get("record"), dict) else payload
    return str(record.get("revision") or "")


def _assert_revision_current(target: Target, item: NeedsYouItem) -> None:
    expected = _displayed_revision(item)
    current = _current_revision(target, item)
    if current != expected:
        raise DismissError(STALE_MESSAGE)


def dismiss_item(
    target: Target,
    item: NeedsYouItem,
    *,
    signer: str | None = None,
    action: str | None = None,
    note: str | None = None,
) -> None:
    """Invoke adaptive-artifacts to clear a human-dismissible Needs-you item.

    Raises DismissRefused for non-human kinds and DismissError when the CLI
    fails or the displayed revision is stale. Does not retry with ``@current``.
    """
    args = dismiss_command(item, signer=signer, action=action, note=note)
    if "@current" in args:
        raise DismissError("internal error: dismiss refused to use @current")
    resolved = _resolve_action(item, action)
    # correct has no --expected-revision; reject create has none — guard both.
    if resolved in (ACTION_SIGN, ACTION_REJECT):
        _assert_revision_current(target, item)
    result = _cli(target, *args)
    if result.returncode != 0:
        _fail(result, " ".join(args[:3]))
