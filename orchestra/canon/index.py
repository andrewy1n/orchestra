"""Lookup tables over a record set: ids and subjects."""

from __future__ import annotations

from collections.abc import Iterable

from orchestra.canon.types import Record

SUPERSEDED = "superseded"


class RecordIndex:
    def __init__(self, records: Iterable[Record] = ()) -> None:
        self.by_id: dict[str, Record] = {}
        self.by_subject: dict[tuple[str, str], list[Record]] = {}
        self.corrected: set[str] = set()
        for record in records:
            self.add(record)

    def add(self, record: Record) -> None:
        self.by_id[record["id"]] = record
        key = (record.get("record_type", ""), record.get("subject", ""))
        self.by_subject.setdefault(key, []).append(record)
        self.corrected.update((record.get("relationships") or {}).get("corrects") or [])

    def subject_exists(self, record_type: str, subject: str) -> bool:
        return bool(self.by_subject.get((record_type, subject)))

    def resolve_subject(self, record_type: str, subject: str) -> Record | None:
        """The latest record of the type with the subject, by recorded_at.

        Superseded and corrected records give way to their successors, which
        can share a timestamp with them.
        """
        candidates = self.by_subject.get((record_type, subject)) or []
        if not candidates:
            return None
        live = [
            r
            for r in candidates
            if r.get("lifecycle_state") != SUPERSEDED and r["id"] not in self.corrected
        ]
        pool = live or candidates
        return max(pool, key=lambda r: (r.get("recorded_at") or "", r["id"]))

    def of_type(self, record_type: str) -> list[Record]:
        return [r for (t, _), items in self.by_subject.items() if t == record_type for r in items]
