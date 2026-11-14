"""Dispatch and landing cost measurements."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from orchestra.canon import record_payload
from orchestra.canon.types import JsonObject, Record


class ExecutionCostError(ValueError):
    """The dispatch cost metadata is invalid."""


@dataclass(frozen=True)
class DispatchMarkers:
    dispatch_id: str
    dispatch_started_at: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_dispatch_markers(now: datetime | None = None) -> DispatchMarkers:
    instant = now if now is not None else utc_now()
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ExecutionCostError("dispatch start must be timezone-aware")
    return DispatchMarkers(
        dispatch_id=str(uuid4()),
        dispatch_started_at=instant.astimezone(timezone.utc).isoformat(timespec="microseconds"),
    )


def _parse_dispatch_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise ExecutionCostError("dispatch start must be an ISO timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ExecutionCostError("dispatch start must be an ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ExecutionCostError("dispatch start must use UTC")
    return parsed.astimezone(timezone.utc)


def landing_cost_fields(
    item: Record,
    evidence: JsonObject,
    received_at: datetime,
) -> JsonObject:
    payload = record_payload(item)
    dispatch_id = payload.get("dispatch_id")
    dispatch_started_at = payload.get("dispatch_started_at")
    fields: JsonObject = {}
    if dispatch_id is not None or dispatch_started_at is not None:
        if not isinstance(dispatch_id, str) or not dispatch_id.strip():
            raise ExecutionCostError("dispatch id must be a non-empty string")
        start = _parse_dispatch_time(dispatch_started_at)
        if received_at.tzinfo is None or received_at.utcoffset() is None:
            raise ExecutionCostError("evidence receipt time must be timezone-aware")
        elapsed = (received_at.astimezone(timezone.utc) - start).total_seconds()
        if elapsed < 0:
            raise ExecutionCostError("dispatch start is later than evidence receipt")
        fields["dispatch_id"] = dispatch_id
        fields["duration_s"] = round(elapsed, 6)
    tokens_total = evidence.get("tokens_total")
    if isinstance(tokens_total, int) and not isinstance(tokens_total, bool):
        fields["tokens_total"] = tokens_total
    return fields
