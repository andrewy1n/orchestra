"""Scan and recovery operations that `orchestra store` runs across components."""

from __future__ import annotations

from collections.abc import Sequence

from orchestra.canon.project import Project
from orchestra.canon.store_commands import RecoveryOutcome, StoreFinding
from orchestra.canon.types import Record
from orchestra.composer.records import scan_composer_records
from orchestra.conductor.evidence_recovery import recover_evidence
from orchestra.conductor.record_scan import scan_phase_records
from orchestra.score.effort import scan_effort_records


def scan(records: Sequence[Record]) -> list[StoreFinding]:
    findings = [
        StoreFinding(f.record_id, f.record_type, f.field, f.message)
        for f in scan_phase_records(records)
    ]
    findings += [
        StoreFinding(f.record_id, f.record_type, f.field, f.message)
        for f in (*scan_effort_records(records), *scan_composer_records(records))
    ]
    return findings


def recover(project: Project, apply: bool) -> RecoveryOutcome:
    report = recover_evidence(project, apply=apply)
    return RecoveryOutcome(
        report={
            "applied": report["applied"],
            "recoverable": list(report["recoverable"]),
            "fresh_proof_required": list(report["fresh_proof_required"]),
            "historical": list(report["historical"]),
        },
        fresh_proof_required=bool(report["fresh_proof_required"]),
    )
