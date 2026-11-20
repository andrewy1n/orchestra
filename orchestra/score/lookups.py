from __future__ import annotations

import contextvars
from collections.abc import Callable, Generator, Iterable, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field

from orchestra.canon import record_payload
from orchestra.canon.query import latest
from orchestra.canon.types import Record

LIVE_WORK_ITEM_STATES = ("planned", "in_progress", "done")


@dataclass
class _Prepared:
    corrected: set[str]
    phases: dict[str, Record]
    by_type: dict[str, list[Record]]
    lists: dict[str, list[Record]] = field(default_factory=dict[str, list[Record]])
    objects: dict[str, object] = field(default_factory=dict[str, object])


_prepared: contextvars.ContextVar[_Prepared | None] = contextvars.ContextVar(
    "prepared_records", default=None
)


def _active() -> _Prepared | None:
    return _prepared.get()


@contextmanager
def prepare_records(records: Sequence[Record]) -> Generator[None, None, None]:
    """Reuse one corrected-id set and type index for repeated reads of ``records``."""
    corrected = _corrected_ids(records)
    by_type: dict[str, list[Record]] = {}
    for record in records:
        by_type.setdefault(record["record_type"], []).append(record)
    token = _prepared.set(
        _Prepared(corrected, _phases_from(records, corrected), by_type)
    )
    try:
        yield
    finally:
        _prepared.reset(token)


def records_of_type(records: Sequence[Record], record_type: str) -> Sequence[Record]:
    prepared = _active()
    if prepared is not None:
        return prepared.by_type.get(record_type, ())
    return [record for record in records if record["record_type"] == record_type]


def cached_object(key: str, build: Callable[[], object]) -> object:
    prepared = _active()
    if prepared is None:
        return build()
    found = prepared.objects.get(key)
    if found is None:
        found = build()
        prepared.objects[key] = found
    return found


def cached_records(
    records: Sequence[Record], key: str, build: Callable[[], list[Record]]
) -> list[Record]:
    prepared = _active()
    if prepared is None:
        return build()
    found = prepared.lists.get(key)
    if found is None:
        found = build()
        prepared.lists[key] = found
    return found


def phase_versions(slug: str, records: Sequence[Record]) -> list[Record]:
    return [
        record
        for record in records
        if record["record_type"] == "score:phase" and record["subject"] == slug
    ]


def current_version(record_type: str, subject: str, records: Sequence[Record]) -> Record | None:
    corrected = corrected_ids(records)
    return latest(
        record
        for record in records
        if record["record_type"] == record_type
        and record["subject"] == subject
        and record["lifecycle_state"] != "superseded"
        and record["id"] not in corrected
    )


def current_phase(slug: str, records: Sequence[Record]) -> Record | None:
    prepared = _active()
    if prepared is not None:
        return prepared.phases.get(slug)
    return current_version("score:phase", slug, records)


def _phases_from(records: Sequence[Record], corrected: set[str]) -> dict[str, Record]:
    order: dict[str, None] = {}
    best: dict[str, Record] = {}
    for record in records:
        if record["record_type"] != "score:phase":
            continue
        subject = record["subject"]
        order.setdefault(subject, None)
        if record["lifecycle_state"] == "superseded" or record["id"] in corrected:
            continue
        current = best.get(subject)
        if current is None or (record.get("recorded_at") or "", record["id"]) > (
            current.get("recorded_at") or "",
            current["id"],
        ):
            best[subject] = record
    return {subject: best[subject] for subject in order if subject in best}


def current_phases(records: Sequence[Record]) -> dict[str, Record]:
    prepared = _active()
    if prepared is not None:
        return prepared.phases
    return _phases_from(records, corrected_ids(records))


def live_work_items(slug: str, records: Sequence[Record]) -> list[Record]:
    return [
        record
        for record in records_of_type(records, "score:work-item")
        if record["lifecycle_state"] in LIVE_WORK_ITEM_STATES
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
    return latest(closing_work_items(slug, records))


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


def _corrected_ids(records: Iterable[Record]) -> set[str]:
    return {
        target
        for record in records
        for target in (record.get("relationships") or {}).get("corrects") or []
    }


def corrected_ids(records: Iterable[Record]) -> set[str]:
    prepared = _active()
    if prepared is not None:
        return prepared.corrected
    return _corrected_ids(records)


def check_run_criteria(acceptance: Record) -> tuple[str, ...]:
    return tuple(dict.fromkeys((acceptance["id"], acceptance["subject"])))
