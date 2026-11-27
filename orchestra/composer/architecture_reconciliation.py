from __future__ import annotations

from collections.abc import Sequence

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.composer.architecture_proposal import (
    ArchitectureProposal,
    RecordPin,
    proposal_for_phase,
)
from orchestra.composer.records import ARCHITECTURE_DECISION, COMPONENT, INTERFACE
from orchestra.score.lookups import direct_corrected_ids, latest_record
from orchestra.score.planning.standing_constraint import RECORD_TYPE as STANDING_CONSTRAINT
from orchestra.score.planning.standing_constraint import is_current_constraint

APPROVAL = "composer:architecture-approval"
RECONCILIATION = "composer:architecture-reconciliation"


def _approved(
    records: Sequence[Record], proposal: ArchitectureProposal, candidate: str
) -> Record | None:
    corrected = direct_corrected_ids(records)
    return latest_record(
        record
        for record in records
        if record["record_type"] == APPROVAL
        and record["id"] not in corrected
        and record["payload"]["proposal"] == proposal.record["id"]
        and record["payload"]["proposal_revision"] == proposal.record["revision"]
        and record["payload"]["candidate"] == candidate
        and str(record["payload"]["approved_by"]).strip()
    )


def _operation(
    current: dict[tuple[str, str], Record],
    record_type: str,
    subject: str,
    base: RecordPin | None,
    payload: JsonObject,
    body: str,
) -> JsonObject:
    record = current.get((record_type, subject))
    if base is None and record is None:
        return {
            "op": "create",
            "type": record_type,
            "subject": subject,
            "payload": payload,
            "body": body,
        }
    if (
        base is None
        or record is None
        or (base.id, base.revision) != (record["id"], record["revision"])
    ):
        raise StoreError(
            f"Architecture change for {subject!r} requires refreshed review of its current version."
        )
    return {
        "op": "supersede",
        "type": record_type,
        "id": base.id,
        "expected_revision": base.revision,
        "payload": payload,
        "body": body,
    }


def _changes(records: Sequence[Record], proposal: ArchitectureProposal) -> list[JsonObject]:
    current = {
        (record["record_type"], record["subject"]): record
        for record in records
        if record["lifecycle_state"] == "active"
    }
    targets = {subject for kind, subject in current if kind in (COMPONENT, INTERFACE)}
    missing_targets = set(proposal.affects) - targets
    if missing_targets:
        raise StoreError(
            f"Architecture proposal requires refreshed review of targets {sorted(missing_targets)}."
        )
    active_constraints = {
        record["subject"] for record in current.values() if is_current_constraint(record)
    }
    operations: list[JsonObject] = []
    for change in proposal.constraints:
        payload = {**change.payload, "retired": change.operation == "retire"}
        if change.operation == "retire":
            active_constraints.discard(change.subject)
        else:
            active_constraints.add(change.subject)
        operations.append(
            _operation(
                current,
                STANDING_CONSTRAINT,
                change.subject,
                change.base,
                payload,
                f"## Basis\n\n{change.basis}\n",
            )
        )
    missing_constraints = set(proposal.enforced_by) - active_constraints
    if missing_constraints:
        raise StoreError(
            f"Architecture proposal requires refreshed review of constraints {sorted(missing_constraints)}."
        )
    operations.append(
        _operation(
            current,
            ARCHITECTURE_DECISION,
            proposal.adr,
            proposal.base_adr,
            {
                "status": "accepted",
                "affects": [*proposal.affects],
                "enforced_by": [*proposal.enforced_by],
            },
            f"## Rationale\n\n{proposal.rationale}\n",
        )
    )
    return operations


def reconcile_architecture(project: Project, phase: str, candidate: str) -> bool:
    token = project.change_token()
    records = project.records()
    if any(
        record["record_type"] == RECONCILIATION and record["subject"] == phase for record in records
    ):
        return False
    proposal = proposal_for_phase(records, phase)
    if proposal is None or proposal.status == "withdrawn":
        return False
    approval = _approved(records, proposal, candidate)
    if approval is None:
        return False
    operations = _changes(records, proposal)
    operations.append(
        {
            "op": "create",
            "type": RECONCILIATION,
            "subject": phase,
            "payload": {"approval": approval["id"]},
        }
    )
    project.apply_at_snapshot(operations, token)
    return True
