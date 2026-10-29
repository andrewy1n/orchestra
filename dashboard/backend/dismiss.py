"""Dismiss human Needs-you items via the canon library.

Human-gate clears always pass the displayed record revision as
``--expected-revision`` (never ``@current``). ``correct`` has no
expected-revision flag, so sign-off guards the revision with a ``get``
before writing.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from orchestra.canon.project import Project
from orchestra.canon.store import StoreError
from dashboard.backend import store
from dashboard.backend.model import NeedsYouItem

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


def _operation(args: list[str]) -> dict[str, Any]:
    operation: dict[str, Any] = {"op": args[0]}
    index = 1
    while index < len(args):
        flag = args[index]
        if index + 1 >= len(args):
            break
        value = args[index + 1]
        index += 2
        if flag == "--type":
            operation["type"] = value
        elif flag == "--id":
            operation["id"] = value
        elif flag == "--subject":
            operation["subject"] = value
        elif flag == "--transition":
            operation["transition"] = value
        elif flag == "--expected-revision":
            operation["expected_revision"] = value
        elif flag == "--payload":
            operation["payload"] = json.loads(value)
        elif flag == "--body":
            operation["body"] = value
    return operation


def _write(target: Project, args: list[str]) -> None:
    operation = _operation(args)
    label = " ".join(args[:3])
    try:
        results = target.apply([operation])
    except OSError as exc:
        raise DismissError(f"cannot apply {operation.get('op')}: {exc}") from exc
    result = results[0] if results else {"ok": False, "message": "no result"}
    if result.get("ok"):
        return
    if result.get("error") == "stale_write":
        raise DismissError(STALE_MESSAGE)
    detail = str(result.get("message") or result.get("error") or "apply failed")
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
    record_type = item.record_type or "score:continuity-question"
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
    claim = f"Plan rejected for {scope}; route to settle-phase or plan-phase"
    payload = {
        "claim": claim,
        "basis": rationale,
        "needs": "human",
        "effort": item.subject,
        "invalidated_when": "approach re-settled or plan-phase re-run",
    }
    body = (
        "## Evidence\n\n"
        f"Plan review rejected from the dashboard for {scope}.\n\n"
        "## Consequence\n\n"
        "Continuity-question remains open; engage should route to settle-phase or plan-phase.\n\n"
        "## Follow-up\n\n"
        f"{rationale}"
    )
    subject = f"plan-rejected:{scope}"[:120]
    return [
        "create", "--type", "tuner:finding", "--subject", subject,
        "--payload", json.dumps(payload), "--body", body,
    ]


def _finding_accept_args(item: NeedsYouItem, note: str | None) -> list[str]:
    record_type = item.record_type or "tuner:finding"
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
    record_type = item.record_type or "tuner:check-run"
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
    """Return the canon argv (after root/store) for this item.

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


def _current_revision(target: Project, item: NeedsYouItem) -> str:
    record_type = item.record_type or {
        "blocking-question": "score:continuity-question",
        "open-question": "score:continuity-question",
        "needs-human": "tuner:finding",
        "unsigned-check": "tuner:check-run",
    }.get(item.kind, "")
    try:
        record = store.stored_record(target, item.id, record_type or None)
    except StoreError as exc:
        raise DismissError(f"get failed: {exc}") from exc
    return str(record.get("revision") or "")


def _assert_revision_current(target: Project, item: NeedsYouItem) -> None:
    expected = _displayed_revision(item)
    current = _current_revision(target, item)
    if current != expected:
        raise DismissError(STALE_MESSAGE)


def dismiss_item(
    target: Project,
    item: NeedsYouItem,
    *,
    signer: str | None = None,
    action: str | None = None,
    note: str | None = None,
) -> None:
    """Invoke canon to clear a human-dismissible Needs-you item.

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
    _write(target, list(args))
