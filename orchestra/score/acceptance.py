from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.fields import optional_blank_text, optional_text_list, required_text
from orchestra.canon.types import JsonObject, Record
from orchestra.score.requirements import acceptance_requirement_ids


@dataclass(frozen=True)
class Acceptance:
    id: str
    subject: str
    phase: str | None
    effort: str
    requirements: tuple[str, ...]
    method: Literal["tdd", "check", "manual"]
    oracle_policy: Literal["none", "frozen"] | None
    verify_command: str
    criteria: str | None
    record: Record


def _method(record: Record, payload: JsonObject) -> Literal["tdd", "check", "manual"]:
    value = required_text(record, payload, "method")
    if value == "tdd" or value == "check" or value == "manual":
        return value
    raise RecordShapeError(record["id"], "method", "must be tdd, check or manual")


def _oracle_policy(record: Record, payload: JsonObject) -> Literal["none", "frozen"] | None:
    value = optional_blank_text(record, payload, "oracle_policy")
    if value is None or value == "none" or value == "frozen":
        return value
    raise RecordShapeError(record["id"], "oracle_policy", "must be none or frozen")


def _requirements(record: Record, payload: JsonObject) -> tuple[str, ...]:
    optional_text_list(record, payload, "requirements")
    optional_blank_text(record, payload, "requirement")
    return tuple(acceptance_requirement_ids(record))


def read_acceptance(record: Record) -> Acceptance:
    payload = record_payload(record)
    return Acceptance(
        id=record["id"],
        subject=record["subject"],
        phase=optional_blank_text(record, payload, "phase"),
        effort=required_text(record, payload, "effort"),
        requirements=_requirements(record, payload),
        method=_method(record, payload),
        oracle_policy=_oracle_policy(record, payload),
        verify_command=required_text(record, payload, "verify_command"),
        criteria=optional_blank_text(record, payload, "criterion"),
        record=record,
    )
