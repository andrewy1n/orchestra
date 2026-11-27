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


class RecordShapeError(ValueError):
    def __init__(self, record_id: str, field: str) -> None:
        super().__init__(f"record {record_id}: required field {field!r} is missing or not text")
        self.record_id = record_id
        self.field = field


def _optional_text(payload: JsonObject, key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def required_text(record: Record, key: str) -> str:
    value = record_payload(record).get(key)
    if not isinstance(value, str):
        raise RecordShapeError(record["id"], key)
    return value


def check_run_facts(record: Record) -> CheckRunFacts:
    payload = record_payload(record)
    return CheckRunFacts(
        id=record["id"],
        criterion_id=required_text(record, "criterion_id"),
        result=required_text(record, "result"),
        method=required_text(record, "method"),
        signed_by=required_text(record, "signed_by"),
        revision=required_text(record, "revision"),
        evidence_kind=_optional_text(payload, "evidence_kind"),
        requirement=_optional_text(payload, "requirement"),
    )


def check_run_failing_nodes(record: Record) -> tuple[str, ...]:
    value = record_payload(record).get("failing_node_ids")
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RecordShapeError(record["id"], "failing_node_ids")
    return tuple(item for item in value if isinstance(item, str))


def finding_facts(record: Record) -> FindingFacts:
    return FindingFacts(claim=required_text(record, "claim"), needs=required_text(record, "needs"))


def observation_text(record: Record) -> str:
    return _optional_text(record_payload(record), "what_was_observed")
