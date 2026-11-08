"""Promote and dismiss backlog items via the canon library."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.backend.snapshot import BacklogItem
from orchestra.canon.project import Project
from orchestra.canon.types import JsonValue

BACKLOG_TYPE = "composer:idea"


class BacklogError(Exception):
    """CLI or validation failure while changing a backlog item."""


class BacklogRefused(BacklogError):
    """Record is not an open backlog item the dashboard can act on."""


@dataclass(frozen=True)
class BacklogResult:
    ok: bool
    message: str = ""


def is_backlog(item: BacklogItem) -> bool:
    record_type = item.record_type or BACKLOG_TYPE
    return record_type == BACKLOG_TYPE and item.status == "open"


def prompt(item: BacklogItem, effort: str | None = None) -> str:
    """Agent prompt to continue with spec (or incidental) after promote."""
    named = effort or item.effort
    return (
        f"Promote backlog item {item.subject} (effort {named}): "
        f"start spec for a new phase, or an incidental work-item if that fits."
    )


def _successor_payload(
    item: BacklogItem, status: str, *, phase: str | None = None
) -> dict[str, JsonValue]:
    payload: dict[str, JsonValue] = {"effort": item.effort, "status": status}
    if item.source:
        payload["source"] = item.source
    chosen = phase if phase is not None else item.phase
    if chosen:
        payload["phase"] = chosen
    return payload


def _supersede(
    target: Project, item: BacklogItem, status: str, *, phase: str | None = None
) -> None:
    if not is_backlog(item):
        raise BacklogRefused(f"cannot act on {item.record_type or 'non-backlog'}")
    operation: dict[str, JsonValue] = {
        "op": "supersede",
        "type": BACKLOG_TYPE,
        "id": item.id,
        "expected_revision": "@current",
        "payload": _successor_payload(item, status, phase=phase),
    }
    try:
        (result,) = target.apply([operation])
    except OSError as exc:
        raise BacklogError(f"cannot apply supersede: {exc}") from exc
    if not result["ok"]:
        detail = str(result.get("message") or result.get("error") or "apply failed")
        raise BacklogError(f"supersede --type {BACKLOG_TYPE} failed: {detail.splitlines()[0]}")


def promote_item(target: Project, item: BacklogItem, *, phase: str | None = None) -> None:
    _supersede(target, item, "promoted", phase=phase)


def dismiss_item(target: Project, item: BacklogItem) -> None:
    _supersede(target, item, "dismissed")
