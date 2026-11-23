from __future__ import annotations

from orchestra.canon import record_payload
from orchestra.canon.types import Record
from orchestra.conductor.verification.requirements import RequirementStatus, all_verified


def _text(record: Record, key: str) -> str:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) else ""


def release_state(record: Record) -> str:
    return _text(record, "state")


def integration_result(record: Record) -> str:
    return _text(record, "result")


def is_release_ready(latest_release: Record | None, statuses: dict[str, RequirementStatus]) -> bool:
    if latest_release is not None and release_state(latest_release) == "ready":
        return True
    return all_verified(statuses)
