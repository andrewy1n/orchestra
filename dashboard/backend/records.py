"""Record-level helpers shared by the dashboard loaders."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

from dashboard.backend import store
from orchestra.canon.project import Project
from orchestra.canon.types import DerivedValues, Record
from orchestra.score.lookups import latest_record
from orchestra.score.planning.effort import record_effort

CHECK_RESULT = {"pass": "passed", "fail": "failed"}
INACTIVE_STATES = ("superseded", "retracted")


def list_records(
    target: Project,
    record_type: str,
    *,
    state: str | None = None,
    payload: Mapping[str, str] | None = None,
) -> list[Record]:
    declared = store.declared_record_types(target)
    if declared is not None and record_type not in declared:
        return []
    return store.list_records(target, record_type, state=state, payload=payload)


def derived_values(record: Record) -> DerivedValues:
    return record.get("derived") or {}


def recorded_at(record: Record) -> datetime:
    stamp = record.get("recorded_at")
    return datetime.fromisoformat(stamp) if stamp else datetime.min.replace(tzinfo=timezone.utc)


def live_records(records: list[Record]) -> list[Record]:
    return [record for record in records if record.get("lifecycle_state") not in INACTIVE_STATES]


def newest_record(records: list[Record]) -> Record | None:
    return latest_record(records)


def records_by_effort(records: list[Record]) -> dict[str | None, list[Record]]:
    grouped: dict[str | None, list[Record]] = {}
    for record in records:
        grouped.setdefault(record_effort(record), []).append(record)
    return grouped
