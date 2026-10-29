"""Promote and dismiss backlog items via the canon library."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from orchestra.canon.project import Project
from dashboard.backend.model import BacklogItem

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
    """Agent prompt to continue with settle-phase (or incidental) after promote."""
    named = effort or item.effort
    return (
        f"Promote backlog item {item.subject} (effort {named}): "
        f"start settle-phase for a new phase, or an incidental work-item if that fits."
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
        elif flag == "--expected-revision":
            operation["expected_revision"] = value
        elif flag == "--payload":
            operation["payload"] = json.loads(value)
    return operation


def _write(target: Project, args: list[str]) -> None:
    operation = _operation(args)
    label = " ".join(args[:3])
    try:
        results = target.apply([operation])
    except OSError as exc:
        raise BacklogError(f"cannot apply {operation.get('op')}: {exc}") from exc
    result = results[0] if results else {"ok": False, "message": "no result"}
    if result.get("ok"):
        return
    detail = str(result.get("message") or result.get("error") or "apply failed")
    raise BacklogError(f"{label} failed: {detail.splitlines()[0]}")


def _successor_payload(item: BacklogItem, status: str, *, phase: str | None = None) -> dict:
    payload: dict = {"effort": item.effort, "status": status}
    if item.source:
        payload["source"] = item.source
    chosen = phase if phase is not None else item.phase
    if chosen:
        payload["phase"] = chosen
    return payload


def _supersede_args(item: BacklogItem, status: str, *, phase: str | None = None) -> list[str]:
    if not is_backlog(item):
        raise BacklogRefused(f"cannot act on {item.record_type or 'non-backlog'}")
    return [
        "supersede", "--type", BACKLOG_TYPE, "--id", item.id,
        "--expected-revision", "@current",
        "--payload", json.dumps(_successor_payload(item, status, phase=phase)),
    ]


def promote_command(item: BacklogItem, *, phase: str | None = None) -> list[str]:
    """Return canon argv to supersede status=promoted."""
    return _supersede_args(item, "promoted", phase=phase)


def dismiss_command(item: BacklogItem) -> list[str]:
    """Return canon argv to supersede status=dismissed."""
    return _supersede_args(item, "dismissed")


def promote_item(target: Project, item: BacklogItem, *, phase: str | None = None) -> None:
    """Supersede an open backlog item to promoted."""
    _write(target, promote_command(item, phase=phase))


def dismiss_item(target: Project, item: BacklogItem) -> None:
    """Supersede an open backlog item to dismissed."""
    _write(target, dismiss_command(item))
