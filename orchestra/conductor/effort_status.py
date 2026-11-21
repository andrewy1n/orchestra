from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.types import Record
from orchestra.score.effort import current_efforts
from orchestra.score.lookups import LIVE_WORK_ITEM_STATES, current_phases, live_work_items

EffortStatus = Literal["closed", "finished", "dormant", "live"]

DORMANT_AFTER = timedelta(days=7)
_LIVE_PHASE_STATES = ("planned", "in_progress", "done")
_ACTIVE_PHASE_STATES = ("planned", "in_progress")


def _text(record: Record, key: str) -> str | None:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) and value else None


def _stamp(record: Record) -> datetime:
    return datetime.fromisoformat(record["recorded_at"].replace("Z", "+00:00"))


def _last_touch(records: Sequence[Record]) -> dict[str, datetime]:
    touched: dict[str, datetime] = {}
    for record in records:
        names: list[str] = []
        named = _text(record, "effort")
        if named is not None:
            names.append(named)
        if record["record_type"] in ("score:effort", "score:continuity-question"):
            names.append(record["subject"])
        for name in names:
            stamp = _stamp(record)
            if name not in touched or stamp > touched[name]:
                touched[name] = stamp
    return touched


def _blocked_efforts(records: Sequence[Record]) -> set[str]:
    return {
        record["subject"]
        for record in records
        if record["record_type"] == "score:continuity-question"
        and record["lifecycle_state"] == "open"
        and record_payload(record).get("blocking") is True
    }


def _all_done(effort: str, records: Sequence[Record], phases: dict[str, Record]) -> bool:
    states: list[str] = []
    for slug, phase in phases.items():
        if _text(phase, "effort") != effort or phase["lifecycle_state"] not in _LIVE_PHASE_STATES:
            continue
        states.append(phase["lifecycle_state"])
        states.extend(
            item["lifecycle_state"]
            for item in live_work_items(slug, records)
            if item["lifecycle_state"] in LIVE_WORK_ITEM_STATES
        )
    return bool(states) and all(state == "done" for state in states)


def effort_statuses(records: Sequence[Record], now: datetime) -> dict[str, EffortStatus]:
    phases = current_phases(records)
    active = {
        name
        for phase in phases.values()
        if phase["lifecycle_state"] in _ACTIVE_PHASE_STATES
        and (name := _text(phase, "effort")) is not None
    }
    blocked = _blocked_efforts(records)
    touched = _last_touch(records)
    result: dict[str, EffortStatus] = {}
    for subject, effort in current_efforts(records).items():
        if effort.status == "closed":
            result[subject] = "closed"
        elif _all_done(subject, records, phases):
            result[subject] = "finished"
        elif (
            subject not in active
            and subject not in blocked
            and subject in touched
            and now - touched[subject] >= DORMANT_AFTER
        ):
            result[subject] = "dormant"
        else:
            result[subject] = "live"
    return result
