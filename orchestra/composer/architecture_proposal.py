from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.fields import optional_text, optional_text_list
from orchestra.canon.sections import body_section
from orchestra.canon.types import JsonObject, Record
from orchestra.composer.records import ARCHITECTURE_DECISION
from orchestra.score.planning.standing_constraint import RECORD_TYPE as STANDING_CONSTRAINT

ARCHITECTURE_PROPOSAL = "composer:architecture-proposal"
CONSTRAINT_CHANGE = "composer:constraint-change"


@dataclass(frozen=True)
class RecordPin:
    id: str
    revision: str


@dataclass(frozen=True)
class ConstraintChange:
    record: Record
    operation: str
    subject: str
    base: RecordPin | None
    payload: JsonObject
    basis: str


@dataclass(frozen=True)
class ArchitectureProposal:
    record: Record
    phase: str
    status: str
    adr: str
    affects: tuple[str, ...]
    enforced_by: tuple[str, ...]
    rationale: str
    base_adr: RecordPin | None
    constraints: tuple[ConstraintChange, ...]


def _text(record: Record, field: str) -> str:
    value = optional_text(record, record["payload"], field)
    if value is None or not value.strip():
        raise RecordShapeError(record["id"], field, "requires non-empty text")
    return value


def _section(record: Record, heading: str) -> str:
    value = body_section(record.get("body", ""), heading)
    if not value:
        raise RecordShapeError(record["id"], "body", f"requires a non-empty {heading} section")
    return value


def _pin(
    record: Record,
    field: str,
    record_type: str,
    subject: str,
    by_id: dict[str, Record],
) -> RecordPin | None:
    fields = record["payload"]
    target = optional_text(record, fields, field)
    revision = optional_text(record, fields, f"{field}_revision")
    if target is None and revision is None:
        return None
    source = by_id.get(target) if target is not None else None
    if (
        source is None
        or source["record_type"] != record_type
        or source["subject"] != subject
        or target is None
        or revision is None
    ):
        raise RecordShapeError(
            record["id"], field, "requires a record id and revision for the target"
        )
    return RecordPin(target, revision)


def _read_constraint_change(record: Record, by_id: dict[str, Record]) -> ConstraintChange:
    fields = record["payload"]
    subject = _text(record, "constraint")
    operation = _text(record, "operation")
    base = _pin(record, "base_constraint", STANDING_CONSTRAINT, subject, by_id)
    payload: JsonObject = {}
    if operation in ("add", "revise"):
        payload = {field: _text(record, field) for field in ("area", "rule", "check")}
        payload["targets"] = list(optional_text_list(record, fields, "targets"))
    elif operation != "retire":
        raise RecordShapeError(record["id"], "operation", "requires add, revise, or retire")
    if (operation == "add") != (base is None):
        raise RecordShapeError(
            record["id"], "base_constraint", "revision and retirement require a baseline"
        )
    return ConstraintChange(record, operation, subject, base, payload, _section(record, "Basis"))


def proposal_for_phase(records: Sequence[Record], phase: str) -> ArchitectureProposal | None:
    active = [
        record
        for record in records
        if record["record_type"] == ARCHITECTURE_PROPOSAL
        and record["lifecycle_state"] == "active"
        and record["payload"].get("phase") == phase
    ]
    if not active:
        return None
    record = active[0]
    if len(active) > 1:
        raise RecordShapeError(record["id"], "phase", "requires a single proposal per phase")
    fields = record["payload"]
    status = _text(record, "status")
    if status not in ("pending", "withdrawn"):
        raise RecordShapeError(record["id"], "status", "requires pending or withdrawn")
    adr = _text(record, "adr")
    affects = optional_text_list(record, fields, "affects")
    if not affects:
        raise RecordShapeError(
            record["id"], "affects", "requires at least one component or interface"
        )
    by_id = {item["id"]: item for item in records}
    changes: list[ConstraintChange] = []
    for change_id in optional_text_list(record, fields, "constraints"):
        change = by_id.get(change_id)
        if change is None or change["record_type"] != CONSTRAINT_CHANGE:
            raise RecordShapeError(
                record["id"], "constraints", f"missing constraint change {change_id}"
            )
        changes.append(_read_constraint_change(change, by_id))
    if len({change.subject for change in changes}) != len(changes):
        raise RecordShapeError(
            record["id"], "constraints", "requires at most one change per constraint"
        )
    return ArchitectureProposal(
        record=record,
        phase=phase,
        status=status,
        adr=adr,
        affects=affects,
        enforced_by=optional_text_list(record, fields, "enforced_by"),
        rationale=_section(record, "Rationale"),
        base_adr=_pin(record, "base_adr", ARCHITECTURE_DECISION, adr, by_id),
        constraints=tuple(changes),
    )
