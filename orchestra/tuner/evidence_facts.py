from __future__ import annotations

from orchestra.canon import record_payload
from orchestra.canon.types import JsonValue, Record

CHECK_RUN_TYPE = "tuner:check-run"
FINDING_TYPE = "tuner:finding"
OBSERVATION_TYPE = "tuner:investigation-observation"

__all__ = [
    "CHECK_RUN_TYPE",
    "FINDING_TYPE",
    "OBSERVATION_TYPE",
    "check_sign_operation",
    "finding_accept_operation",
    "finding_basis",
    "plan_rejection_operation",
]


def finding_basis(record: Record) -> str:
    basis = record_payload(record).get("basis")
    return basis if isinstance(basis, str) else ""


def finding_accept_operation(
    record_type: str, record_id: str, revision: str, note: str | None
) -> dict[str, JsonValue]:
    payload: dict[str, JsonValue] = {"needs": "none"}
    if note:
        payload["resolution_note"] = note
    return {
        "op": "update",
        "type": record_type,
        "id": record_id,
        "expected_revision": revision,
        "payload": payload,
    }


def check_sign_operation(
    record_type: str, record_id: str, revision: str, signer: str, note: str | None
) -> dict[str, JsonValue]:
    payload: dict[str, JsonValue] = {"signed_by": signer}
    if note:
        payload["signed_note"] = note
    return {
        "op": "correct",
        "type": record_type,
        "id": record_id,
        "expected_revision": revision,
        "payload": payload,
    }


def plan_rejection_operation(scope: str, note: str | None, effort: str) -> dict[str, JsonValue]:
    rationale = (note or "").strip() or "Rejected from dashboard Needs-you"
    payload: dict[str, JsonValue] = {
        "claim": f"Plan rejected for {scope}; route to spec or tasks",
        "basis": rationale,
        "needs": "human",
        "effort": effort,
        "invalidated_when": "approach re-settled or tasks re-run",
    }
    body = (
        "## Evidence\n\n"
        f"Plan review rejected from the dashboard for {scope}.\n\n"
        "## Consequence\n\n"
        "Continuity-question remains open; engage should route to spec or tasks.\n\n"
        "## Follow-up\n\n"
        f"{rationale}"
    )
    subject = ("plan-rejected:" + "-".join(scope.split()))[:120]
    return {
        "op": "create",
        "type": FINDING_TYPE,
        "subject": subject,
        "payload": payload,
        "body": body,
    }
