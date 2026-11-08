"""Read `conductor:landing` records written by `orchestra land`."""

from __future__ import annotations

from collections.abc import Sequence

from orchestra.canon import record_payload
from orchestra.canon.types import Record

LANDING = "conductor:landing"


def latest_landing(records: Sequence[Record], phase: str) -> Record | None:
    """Return the newest landing record for a phase, or None."""
    found = [
        record
        for record in records
        if record["record_type"] == LANDING and record_payload(record).get("phase") == phase
    ]
    if not found:
        return None
    return max(enumerate(found), key=lambda pair: (pair[1].get("recorded_at", ""), pair[0]))[1]
