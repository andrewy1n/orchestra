from __future__ import annotations

from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import JsonObject, Record

WORK_ITEM_TYPE = "score:work-item"
PHASE_TYPE = "score:phase"
ACCEPTANCE_TYPE = "score:acceptance"
DECISION_TYPE = "score:decision"


@dataclass(frozen=True)
class AcceptanceFacts:
    criterion: str
    method: str
    verify_command: str


def _text(payload: JsonObject, key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def acceptance_facts(record: Record) -> AcceptanceFacts:
    payload = record_payload(record)
    return AcceptanceFacts(
        criterion=_text(payload, "criterion"),
        method=_text(payload, "method"),
        verify_command=_text(payload, "verify_command"),
    )
