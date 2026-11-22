from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import JsonObject, Record
from orchestra.score.lookups import record_order

_INACTIVE = ("superseded", "retracted")


@dataclass(frozen=True)
class AssessmentFacts:
    phase: str
    requirement: str
    status: str
    level: str
    next: str
    confidence: str


def _text(payload: JsonObject, key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def assessment_facts(record: Record) -> AssessmentFacts:
    payload = record_payload(record)
    return AssessmentFacts(
        phase=_text(payload, "phase"),
        requirement=_text(payload, "requirement"),
        status=_text(payload, "status"),
        level=_text(payload, "level"),
        next=_text(payload, "next"),
        confidence=_text(payload, "confidence"),
    )


def latest_assessments(records: Sequence[Record], phase: str) -> dict[str, Record]:
    latest: dict[str, Record] = {}
    for record in sorted(records, key=record_order):
        if record["lifecycle_state"] in _INACTIVE:
            continue
        facts = assessment_facts(record)
        if facts.phase == phase:
            latest[facts.requirement] = record
    return latest
