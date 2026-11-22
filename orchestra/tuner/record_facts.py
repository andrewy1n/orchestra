from __future__ import annotations

from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import JsonObject, Record


@dataclass(frozen=True)
class CheckRunFacts:
    id: str
    criterion_id: str
    result: str
    method: str
    signed_by: str
    revision: str
    evidence_kind: str
    requirement: str = ""


@dataclass(frozen=True)
class FindingFacts:
    claim: str
    needs: str


def _text(payload: JsonObject, key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def check_run_facts(record: Record) -> CheckRunFacts:
    payload = record_payload(record)
    return CheckRunFacts(
        id=record["id"],
        criterion_id=_text(payload, "criterion_id"),
        result=_text(payload, "result"),
        method=_text(payload, "method"),
        signed_by=_text(payload, "signed_by"),
        revision=_text(payload, "revision"),
        evidence_kind=_text(payload, "evidence_kind"),
        requirement=_text(payload, "requirement"),
    )


def finding_facts(record: Record) -> FindingFacts:
    payload = record_payload(record)
    return FindingFacts(claim=_text(payload, "claim"), needs=_text(payload, "needs"))


def observation_text(record: Record) -> str:
    return _text(record_payload(record), "what_was_observed")
