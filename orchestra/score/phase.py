from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import JsonObject, Record
from orchestra.score.lookups import current_phase


@dataclass(frozen=True)
class Phase:
    id: str
    subject: str
    title: str
    ordinal: int
    effort: str
    milestone: str | None
    weight: Literal["light", "full"] | None
    oracle_policy: Literal["none", "frozen"] | None
    body: str
    record: Record


def _required_text(record: Record, payload: JsonObject, field: str) -> str:
    if field not in payload:
        raise RecordShapeError(record["id"], field, "is required")
    value = payload[field]
    if not isinstance(value, str):
        raise RecordShapeError(record["id"], field, "must be a string")
    return value


def _required_ordinal(record: Record, payload: JsonObject) -> int:
    if "ordinal" not in payload:
        raise RecordShapeError(record["id"], "ordinal", "is required")
    value = payload["ordinal"]
    if isinstance(value, bool) or not isinstance(value, int):
        raise RecordShapeError(record["id"], "ordinal", "must be an integer")
    return value


def _optional_text(record: Record, payload: JsonObject, field: str) -> str | None:
    if field not in payload:
        return None
    value = payload[field]
    if not isinstance(value, str):
        raise RecordShapeError(record["id"], field, "must be a string")
    return value


def _weight(record: Record, payload: JsonObject) -> Literal["light", "full"] | None:
    value = _optional_text(record, payload, "weight")
    if value is None or value == "light" or value == "full":
        return value
    raise RecordShapeError(record["id"], "weight", "must be light or full")


def _oracle_policy(record: Record, payload: JsonObject) -> Literal["none", "frozen"] | None:
    value = _optional_text(record, payload, "oracle_policy")
    if value is None or value == "none" or value == "frozen":
        return value
    raise RecordShapeError(record["id"], "oracle_policy", "must be none or frozen")


def _body(record: Record) -> str:
    body: object = record.get("body", "")
    if not isinstance(body, str):
        raise RecordShapeError(record["id"], "body", "must be a string")
    return body


def read_phase(record: Record) -> Phase:
    payload = record_payload(record)
    return Phase(
        id=record["id"],
        subject=record["subject"],
        title=_required_text(record, payload, "title"),
        ordinal=_required_ordinal(record, payload),
        effort=_required_text(record, payload, "effort"),
        milestone=_optional_text(record, payload, "milestone"),
        weight=_weight(record, payload),
        oracle_policy=_oracle_policy(record, payload),
        body=_body(record),
        record=record,
    )


def current_phase_model(slug: str, records: Sequence[Record]) -> Phase | None:
    record = current_phase(slug, records)
    return read_phase(record) if record is not None else None
