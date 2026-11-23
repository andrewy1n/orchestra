from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.fields import optional_text, required_int, required_text
from orchestra.canon.types import JsonObject, Record
from orchestra.score.lookups import current_phase, current_phases


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


def _weight(record: Record, payload: JsonObject) -> Literal["light", "full"] | None:
    value = optional_text(record, payload, "weight")
    if value is None or value == "light" or value == "full":
        return value
    raise RecordShapeError(record["id"], "weight", "must be light or full")


def _oracle_policy(record: Record, payload: JsonObject) -> Literal["none", "frozen"] | None:
    value = optional_text(record, payload, "oracle_policy")
    if value is None or value == "none" or value == "frozen":
        return value
    raise RecordShapeError(record["id"], "oracle_policy", "must be none or frozen")


def _body(record: Record) -> str:
    body: object = record.get("body", "")
    if not isinstance(body, str):
        raise RecordShapeError(record["id"], "body", "must be a string")
    return body


def phase_title(record: Record) -> str:
    title = record_payload(record).get("title")
    return title if isinstance(title, str) and title else record["subject"]


def read_phase(record: Record) -> Phase:
    payload = record_payload(record)
    return Phase(
        id=record["id"],
        subject=record["subject"],
        title=required_text(record, payload, "title"),
        ordinal=required_int(record, payload, "ordinal"),
        effort=required_text(record, payload, "effort"),
        milestone=optional_text(record, payload, "milestone"),
        weight=_weight(record, payload),
        oracle_policy=_oracle_policy(record, payload),
        body=_body(record),
        record=record,
    )


def current_phase_model(slug: str, records: Sequence[Record]) -> Phase | None:
    record = current_phase(slug, records)
    return read_phase(record) if record is not None else None


def structured_phases(specs: Sequence[Record], phases: Sequence[Record]) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for record in specs:
        if record["lifecycle_state"] in ("superseded", "retracted"):
            continue
        payload = record_payload(record)
        effort, phase = payload.get("effort"), payload.get("phase")
        if isinstance(effort, str) and effort and isinstance(phase, str) and phase:
            found.add((effort, phase))
    for current in current_phases(phases).values():
        model = read_phase(current)
        if model.weight == "light":
            found.add((model.effort, model.subject))
    return found
