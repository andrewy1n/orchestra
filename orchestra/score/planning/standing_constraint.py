from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.fields import required_text
from orchestra.canon.sections import body_section
from orchestra.canon.types import Record

RECORD_TYPE = "score:standing-constraint"


@dataclass(frozen=True)
class StandingConstraint:
    id: str
    name: str
    area: str
    rule: str
    check: str
    basis: str


def _basis(record: Record) -> str:
    body: object = record.get("body", "")
    if not isinstance(body, str):
        raise RecordShapeError(record["id"], "body", "must be a string")
    return body_section(body, "Basis")


def read_standing_constraint(record: Record) -> StandingConstraint:
    payload = record_payload(record)
    return StandingConstraint(
        id=record["id"],
        name=record["subject"],
        area=required_text(record, payload, "area"),
        rule=required_text(record, payload, "rule"),
        check=required_text(record, payload, "check"),
        basis=_basis(record),
    )


def applicable(records: Sequence[Record], area: str) -> list[StandingConstraint]:
    declared = (
        read_standing_constraint(record)
        for record in records
        if record["record_type"] == RECORD_TYPE and record["lifecycle_state"] == "active"
    )
    return [constraint for constraint in declared if constraint.area == area]


def declared_areas(records: Sequence[Record]) -> list[str]:
    return sorted(
        {
            read_standing_constraint(record).area
            for record in records
            if record["record_type"] == RECORD_TYPE and record["lifecycle_state"] == "active"
        }
    )
