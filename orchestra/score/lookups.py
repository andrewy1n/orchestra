from __future__ import annotations

from collections.abc import Sequence

from orchestra.canon import record_payload
from orchestra.canon.query import latest
from orchestra.canon.types import Record

LIVE_WORK_ITEM_STATES = ("planned", "in_progress", "done")


def current_phase(slug: str, records: Sequence[Record]) -> Record | None:
    phases = [
        record
        for record in records
        if record["record_type"] == "score:phase" and record["subject"] == slug
    ]
    corrected = {
        target
        for record in records
        for target in (record.get("relationships") or {}).get("corrects") or []
    }
    return latest(
        phase
        for phase in phases
        if phase["lifecycle_state"] != "superseded" and phase["id"] not in corrected
    )


def live_work_items(slug: str, records: Sequence[Record]) -> list[Record]:
    return [
        record
        for record in records
        if record["record_type"] == "score:work-item"
        and record["lifecycle_state"] in LIVE_WORK_ITEM_STATES
        and record_payload(record).get("phase") == slug
    ]


def dependencies(item: Record) -> list[str]:
    value = record_payload(item).get("depends_on")
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, str)]


def closing_work_item(slug: str, records: Sequence[Record]) -> Record | None:
    items = live_work_items(slug, records)
    if len(items) < 2:
        return None
    closing: list[Record] = []
    for item in items:
        named = set(dependencies(item))
        others = [other for other in items if other["id"] != item["id"]]
        if all(other["subject"] in named or other["id"] in named for other in others):
            closing.append(item)
    return latest(closing)


def _matches(acceptance: Record, item: Record) -> bool:
    subject = item["subject"]
    return acceptance["subject"] == subject or acceptance["subject"].startswith(f"{subject}-")


def acceptances_of(
    slug: str,
    item: Record,
    work_items: Sequence[Record],
    acceptances: Sequence[Record],
) -> list[Record]:
    phase_items = live_work_items(slug, work_items)
    owned: list[Record] = []
    for acceptance in acceptances:
        if (
            acceptance["record_type"] != "score:acceptance"
            or acceptance["lifecycle_state"] != "active"
            or record_payload(acceptance).get("phase") != slug
        ):
            continue
        matching = [candidate for candidate in phase_items if _matches(acceptance, candidate)]
        if not matching:
            continue
        owner = max(matching, key=lambda candidate: len(candidate["subject"]))
        if owner["id"] == item["id"]:
            owned.append(acceptance)
    return owned
