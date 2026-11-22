from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import JsonObject, Record
from orchestra.score.lookups import record_order

_INACTIVE = ("superseded", "retracted")
_UPSTREAM_NEXT = frozenset({"specify", "design", "plan"})


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


@dataclass(frozen=True)
class AssessmentSummary:
    text: str
    failed: bool


def assessment_summary(record: Record, by_id: Mapping[str, Record]) -> AssessmentSummary:
    facts = assessment_facts(record)
    text = f"{facts.requirement} {facts.status} {facts.next}"
    if facts.next in _UPSTREAM_NEXT:
        text += " upstream"
    links = (record.get("relationships") or {}).get("supersedes") or []
    previous = by_id.get(links[0]) if links else None
    if previous is not None:
        old = assessment_facts(previous).level
        if old != facts.level:
            text += f" level {old} to {facts.level}"
    return AssessmentSummary(text, facts.status in ("failed", "blocked"))
