"""Dismiss human Needs-you items via the Canon library."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dashboard.backend import store
from dashboard.backend.snapshot import NeedsYouItem
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonValue

HUMAN_DISMISSIBLE = frozenset(
    {
        "blocking-question",
        "open-question",
        "needs-human",
        "unsigned-check",
    }
)

DEFAULT_SIGNER_ENV = "ORCHESTRA_SIGNED_BY"

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


def _write(target: Project, operation: dict[str, JsonValue]) -> None:
    label = f"{operation['op']} --type {operation['type']}"
    try:
        (result,) = target.apply([operation])
    except OSError as exc:
        raise DismissError(f"cannot apply {operation.get('op')}: {exc}") from exc
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
    if (
        (
            item.kind in ("blocking-question", "open-question")
            and resolved not in (ACTION_APPROVE, ACTION_REJECT)
        )
        or (item.kind == "needs-human" and resolved != ACTION_ACCEPT)
        or (item.kind == "unsigned-check" and resolved != ACTION_SIGN)
    ):
        raise DismissError(f"unsupported action {resolved!r} for {item.kind}")
    return resolved


def _question_approve(item: NeedsYouItem, note: str | None) -> dict[str, JsonValue]:
    operation: dict[str, JsonValue] = {
        "op": "update",
        "type": item.record_type or "score:continuity-question",
        "id": item.id,
        "transition": "answered",
        "expected_revision": _displayed_revision(item),
    }
    if note:
        operation["payload"] = {"answer": note}
    return operation


def _question_reject(item: NeedsYouItem, note: str | None) -> dict[str, JsonValue]:
    """Leave the continuity-question open; create a needs:human routing finding."""
    scope = item.text or item.subject
    rationale = (note or "").strip() or "Rejected from dashboard Needs-you"
    claim = f"Plan rejected for {scope}; route to settle-phase or plan-phase"
    payload: dict[str, JsonValue] = {
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
    subject = "plan-rejected:" + "-".join(scope.split())
    subject = subject[:120]
    return {
        "op": "create",
        "type": "tuner:finding",
        "subject": subject,
        "payload": payload,
        "body": body,
    }


def _finding_accept(item: NeedsYouItem, note: str | None) -> dict[str, JsonValue]:
    payload: dict[str, JsonValue] = {"needs": "none"}
    if note:
        payload["resolution_note"] = note
    return {
        "op": "update",
        "type": item.record_type or "tuner:finding",
        "id": item.id,
        "expected_revision": _displayed_revision(item),
        "payload": payload,
    }


def _check_sign(item: NeedsYouItem, signer: str, note: str | None) -> dict[str, JsonValue]:
    payload: dict[str, JsonValue] = {"signed_by": signer}
    if note:
        payload["signed_note"] = note
    return {
        "op": "correct",
        "type": item.record_type or "tuner:check-run",
        "id": item.id,
        "payload": payload,
    }


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
    if not is_dismissible(item.kind):
        raise DismissRefused(f"cannot dismiss {item.kind}")
    resolved = _resolve_action(item, action)
    if resolved in (ACTION_SIGN, ACTION_REJECT):
        _assert_revision_current(target, item)
    if resolved == ACTION_APPROVE:
        operation = _question_approve(item, note)
    elif resolved == ACTION_REJECT:
        operation = _question_reject(item, note)
    elif resolved == ACTION_ACCEPT:
        operation = _finding_accept(item, note)
    else:
        operation = _check_sign(item, signer or default_signer(), note)
    _write(target, operation)
