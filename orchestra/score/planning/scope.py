from __future__ import annotations

from collections.abc import Sequence

from orchestra.canon import record_payload
from orchestra.canon.types import Record

_INACTIVE = ("superseded", "retracted")


def records_for_phase(records: Sequence[Record], phase: str, effort: str) -> list[Record]:
    matched: list[Record] = []
    for record in records:
        if record["lifecycle_state"] in _INACTIVE:
            continue
        payload = record_payload(record)
        record_effort = payload.get("effort")
        if record_effort and record_effort != effort:
            continue
        if payload.get("phase") == phase:
            matched.append(record)
    return matched


def spec_weight(record: Record) -> str:
    weight = record_payload(record).get("weight")
    return weight if isinstance(weight, str) else ""


def design_decisions(record: Record) -> tuple[str, ...]:
    decisions = record_payload(record).get("decisions")
    if not isinstance(decisions, list):
        return ()
    return tuple(item for item in decisions if isinstance(item, str))


def spec_requirements(record: Record) -> tuple[str, ...]:
    requirements = record_payload(record).get("requirements")
    if not isinstance(requirements, list):
        return ()
    return tuple(item for item in requirements if isinstance(item, str))
