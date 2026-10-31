"""Record-level helpers shared by the dashboard loaders."""

from __future__ import annotations

from orchestra.canon import record_payload
from datetime import datetime, timezone
from typing import Any

from orchestra.canon.project import Project
from dashboard.backend import store
from dashboard.backend.store import ModelError


CHECK_RESULT = {"pass": "passed", "fail": "failed"}
SOFT_TYPES = frozenset(
    {
        "score:specification",
        "score:design",
        "conductor:assessment",
        "conductor:integration-report",
        "conductor:proof-packet",
        "conductor:release",
        "score:position",
        "composer:idea",
        "score:milestone",
        "composer:area",
    }
)
INACTIVE_STATES = ("superseded", "retracted")


def _list(
    target: Project,
    record_type: str,
    *,
    state: str | None = None,
    payload: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    declared = store.declared_record_types(target)
    if declared is not None and record_type not in declared:
        return []
    try:
        return store.list_records(target, record_type, state=state, payload=payload)
    except ModelError:
        if record_type in SOFT_TYPES:
            return []
        raise


def _merge_aliases(goals: list[dict[str, Any]]) -> dict[str, str]:
    return {
        old: goal["subject"]
        for goal in goals
        for old in record_payload(goal).get("merged_from") or []
    }


def _remapped(records: list[dict[str, Any]], aliases: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            **record,
            "payload": {
                **record_payload(record),
                "effort": aliases[record_payload(record)["effort"]],
            },
        }
        if record_payload(record).get("effort") in aliases
        else record
        for record in records
    ]


def _derived(record: dict[str, Any]) -> dict[str, Any]:
    return record.get("derived") or {}


def _recorded_at(record: dict[str, Any]) -> datetime:
    stamp = record.get("recorded_at")
    return datetime.fromisoformat(stamp) if stamp else datetime.min.replace(tzinfo=timezone.utc)


def _items(value: Any) -> list[str]:
    if not value:
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _section(body: str, heading: str) -> str:
    collected: list[str] = []
    collecting = False
    target = heading.strip().lower()
    for line in (body or "").splitlines():
        if line.startswith("## "):
            if collecting:
                break
            collecting = line[3:].strip().lower() == target
            continue
        if collecting:
            collected.append(line)
    return "\n".join(collected).strip()


def _live(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if record.get("lifecycle_state") not in INACTIVE_STATES]


def _newest(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    return max(records, key=_recorded_at) if records else None


def _by_effort(
    records: list[dict[str, Any]], key: str = "effort"
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        effort = record["subject"] if key == "subject" else record_payload(record).get(key)
        grouped.setdefault(effort, []).append(record)
    return grouped
