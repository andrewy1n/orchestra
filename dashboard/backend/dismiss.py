"""Dismiss human Needs-you items via the Canon library."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dashboard.backend import store
from dashboard.backend.snapshot import NeedsYouItem
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonValue
from orchestra.score.workflow.continuity import question_answer_operation
from orchestra.score.workflow.workflow_blockers import (
    CHECK_RUN_TYPE,
    CLEARS,
    FINDING_TYPE,
    QUESTION_TYPE,
)
from orchestra.tuner.evidence_facts import (
    check_sign_operation,
    finding_accept_operation,
    plan_rejection_operation,
)

HUMAN_DISMISSIBLE = frozenset(CLEARS)

DEFAULT_SIGNER_ENV = "ORCHESTRA_SIGNED_BY"

ACTION_APPROVE = "approve"
ACTION_REJECT = "reject"
ACTION_SIGN = "sign"
ACTION_ACCEPT = "accept"

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
    signer = os.environ.get(DEFAULT_SIGNER_ENV, "").strip()
    if not signer:
        raise DismissError(f"{DEFAULT_SIGNER_ENV} is required")
    return signer


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
    return question_answer_operation(
        item.record_type or QUESTION_TYPE, item.id, _displayed_revision(item), note
    )


def _question_reject(item: NeedsYouItem, note: str | None) -> dict[str, JsonValue]:
    """Leave the continuity-question open; create a needs:human routing finding."""
    return plan_rejection_operation(item.text or item.subject, note, item.subject)


def _finding_accept(item: NeedsYouItem, note: str | None) -> dict[str, JsonValue]:
    return finding_accept_operation(
        item.record_type or FINDING_TYPE, item.id, _displayed_revision(item), note
    )


def _check_sign(item: NeedsYouItem, signer: str, note: str | None) -> dict[str, JsonValue]:
    return check_sign_operation(
        item.record_type or CHECK_RUN_TYPE, item.id, _displayed_revision(item), signer, note
    )


def _current_revision(target: Project, item: NeedsYouItem) -> str:
    record_type = item.record_type or CLEARS.get(item.kind, "")
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
    if resolved == ACTION_REJECT:
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
