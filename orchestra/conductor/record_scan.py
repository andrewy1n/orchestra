from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import Record
from orchestra.conductor.landing import LANDING, PROOF_PACKET, read_landing, read_proof_packet
from orchestra.score.lookups import corrected_ids, current_phases
from orchestra.score.phase import read_phase


@dataclass(frozen=True)
class ScanFinding:
    record_id: str
    record_type: str
    field: str
    message: str


_EVENT_READERS: dict[str, Callable[[Record], object]] = {
    LANDING: read_landing,
    PROOF_PACKET: read_proof_packet,
}


def _rejection(reader: Callable[[Record], object], record: Record) -> ScanFinding | None:
    try:
        reader(record)
    except RecordShapeError as error:
        return ScanFinding(error.record_id, record["record_type"], error.field, error.message)
    return None


def scan_phase_records(records: Sequence[Record]) -> list[ScanFinding]:
    """Return a finding for each live phase, landing and proof packet the typed readers reject."""
    corrected = corrected_ids(records)
    candidates = [(read_phase, record) for record in current_phases(records).values()]
    candidates += [
        (_EVENT_READERS[record["record_type"]], record)
        for record in records
        if record["record_type"] in _EVENT_READERS and record["id"] not in corrected
    ]
    found = (_rejection(reader, record) for reader, record in candidates)
    return [finding for finding in found if finding is not None]
