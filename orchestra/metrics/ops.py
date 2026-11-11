from __future__ import annotations

from collections import Counter

from orchestra.canon import record_payload
from orchestra.canon.backend import open_backend
from orchestra.canon.project import Project
from orchestra.canon.types import Record


def _text(record: Record, key: str) -> str:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) else ""


def tasks_of(records: list[Record], phase: str) -> list[Record]:
    chosen: dict[str, Record] = {}
    for r in records:
        if r["record_type"] != "score:work-item" or _text(r, "phase") != phase:
            continue
        current = chosen.get(r["subject"])
        rank = (r["lifecycle_state"] != "superseded", r["recorded_at"])
        if current is None or rank >= (
            current["lifecycle_state"] != "superseded",
            current["recorded_at"],
        ):
            chosen[r["subject"]] = r
    return [r for r in chosen.values() if r["lifecycle_state"] != "withdrawn"]


def belongs_to(
    record: Record, phase: str, acceptance_ids: set[str], task_subjects: set[str]
) -> bool:
    kind = record["record_type"]
    if kind == "tuner:check-run":
        return _text(record, "criterion_id") in acceptance_ids or record["subject"].startswith(
            phase + "-"
        )
    if kind == "conductor:execution-report":
        return _text(record, "work_item") in task_subjects
    return _text(record, "phase") == phase or (kind == "score:phase" and record["subject"] == phase)


def count_operations(project: Project, phase: str) -> tuple[Counter[str], int]:
    records = project.records()
    tasks = tasks_of(records, phase)
    subjects = {t["subject"] for t in tasks}
    acceptance_ids = {
        r["id"]
        for r in records
        if r["record_type"] == "score:acceptance" and _text(r, "phase") == phase
    }
    members = {
        r["id"]: r["record_type"] for r in records if belongs_to(r, phase, acceptance_ids, subjects)
    }
    counts: Counter[str] = Counter()
    for record_id, chain in open_backend(
        project.store_path, read_only=project.read_only
    ).iter_chains():
        if record_id in members:
            counts[members[record_id]] += len(chain)
    return counts, len(tasks)
