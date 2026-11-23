from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import Record
from orchestra.conductor.landing import LANDING, PROOF_PACKET, read_landing, read_proof_packet
from orchestra.score.lookups import corrected_ids, current_phases
from orchestra.score.planning.acceptance import read_acceptance
from orchestra.score.planning.phase import read_phase
from orchestra.score.planning.requirements import SPECIFICATION, read_requirements
from orchestra.tuner.records import (
    read_check_run,
    read_evidence_binding,
    read_finding,
)

ACCEPTANCE = "score:acceptance"
CHECK_RUN = "tuner:check-run"
FINDING = "tuner:finding"
EVIDENCE_BINDING = "tuner:evidence-binding"

_DEAD_STATES = ("superseded", "retracted")


@dataclass(frozen=True)
class ScanFinding:
    record_id: str
    record_type: str
    field: str
    message: str


def _read_check_run_record(record: Record) -> object:
    return read_check_run(record, record.get("derived", {}).get("write_order", 0))


_EVENT_READERS: dict[str, Callable[[Record], object]] = {
    LANDING: read_landing,
    PROOF_PACKET: read_proof_packet,
    CHECK_RUN: _read_check_run_record,
}

_LIVE_READERS: dict[str, Callable[[Record], object]] = {
    ACCEPTANCE: read_acceptance,
    FINDING: read_finding,
    EVIDENCE_BINDING: read_evidence_binding,
    SPECIFICATION: read_requirements,
}


def _rejection(reader: Callable[[Record], object], record: Record) -> ScanFinding | None:
    try:
        reader(record)
    except RecordShapeError as error:
        return ScanFinding(error.record_id, record["record_type"], error.field, error.message)
    return None


def scan_phase_records(records: Sequence[Record]) -> list[ScanFinding]:
    """Return a finding for each live record the typed readers reject."""
    corrected = corrected_ids(records)
    candidates = [(read_phase, record) for record in current_phases(records).values()]
    candidates += [
        (read_requirements, record)
        for record in current_phases(records).values()
        if record["payload"].get("weight") == "light"
    ]
    candidates += [
        (_EVENT_READERS[record["record_type"]], record)
        for record in records
        if record["record_type"] in _EVENT_READERS and record["id"] not in corrected
    ]
    candidates += [
        (_LIVE_READERS[record["record_type"]], record)
        for record in records
        if record["record_type"] in _LIVE_READERS
        and record["lifecycle_state"] not in _DEAD_STATES
        and record["id"] not in corrected
    ]
    found = (_rejection(reader, record) for reader, record in candidates)
    return [finding for finding in found if finding is not None]
