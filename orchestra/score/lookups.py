from __future__ import annotations

from collections.abc import Iterable, Sequence

from orchestra.canon import record_payload
from orchestra.canon.types import Record

LIVE_WORK_ITEM_STATES = ("planned", "in_progress", "done")


def record_order(record: Record) -> tuple[str, int, str]:
    return (
        record.get("recorded_at") or "",
        record.get("derived", {}).get("write_order", 0),
        record["id"],
    )


def latest_record(records: Iterable[Record]) -> Record | None:
    return max(records, key=record_order, default=None)


def phase_versions(slug: str, records: Sequence[Record]) -> list[Record]:
    return [
        record
        for record in records
        if record["record_type"] == "score:phase" and record["subject"] == slug
    ]


def current_version(record_type: str, subject: str, records: Sequence[Record]) -> Record | None:
    corrected = corrected_ids(records)
    return latest_record(
        record
        for record in records
        if record["record_type"] == record_type
        and record["subject"] == subject
        and record["lifecycle_state"] != "superseded"
        and record["id"] not in corrected
    )


def current_phase(slug: str, records: Sequence[Record]) -> Record | None:
    return current_version("score:phase", slug, records)


def current_phases(records: Sequence[Record]) -> dict[str, Record]:
    slugs = dict.fromkeys(
        record["subject"] for record in records if record["record_type"] == "score:phase"
    )
    found = {slug: current_phase(slug, records) for slug in slugs}
    return {slug: record for slug, record in found.items() if record is not None}


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


def closing_work_items(slug: str, records: Sequence[Record]) -> list[Record]:
    items = live_work_items(slug, records)
    if len(items) < 2:
        return []
    closing: list[Record] = []
    for item in items:
        named = set(dependencies(item))
        others = [other for other in items if other["id"] != item["id"]]
        if all(other["subject"] in named or other["id"] in named for other in others):
            closing.append(item)
    return closing


def closing_work_item(slug: str, records: Sequence[Record]) -> Record | None:
    return latest_record(closing_work_items(slug, records))


def _matches(subject: str, item: Record) -> bool:
    name = item["subject"]
    return subject == name or subject.startswith(f"{name}-")


def owning_work_item(subject: str, work_items: Sequence[Record]) -> Record | None:
    matching = [item for item in work_items if _matches(subject, item)]
    return max(matching, key=lambda item: len(item["subject"]), default=None)


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
        owner = owning_work_item(acceptance["subject"], phase_items)
        if owner is not None and owner["id"] == item["id"]:
            owned.append(acceptance)
    return owned


def corrected_ids(records: Iterable[Record]) -> set[str]:
    return {
        target
        for record in records
        for target in (record.get("relationships") or {}).get("corrects") or []
    }


def check_run_criteria(acceptance: Record) -> tuple[str, ...]:
    return tuple(dict.fromkeys((acceptance["id"], acceptance["subject"])))
