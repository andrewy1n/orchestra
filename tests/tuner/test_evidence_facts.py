from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.tuner.evidence_facts import (
    check_sign_operation,
    finding_accept_operation,
    finding_basis,
    plan_rejection_operation,
)


def _record(record_type: str, payload: JsonObject, subject: str = "s") -> Record:
    return {
        "id": f"<{record_type}:{subject}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00Z",
    }


def test_finding_basis_reads_text_and_defaults_to_empty() -> None:
    assert finding_basis(_record("tuner:finding", {"basis": "seen"})) == "seen"
    assert finding_basis(_record("tuner:finding", {"basis": 4})) == ""
    assert finding_basis(_record("tuner:finding", {})) == ""


def test_finding_accept_operation_sets_needs_none_with_optional_note() -> None:
    assert finding_accept_operation("tuner:finding", "f1", "r2", "ok") == {
        "op": "update",
        "type": "tuner:finding",
        "id": "f1",
        "expected_revision": "r2",
        "payload": {"needs": "none", "resolution_note": "ok"},
    }
    assert finding_accept_operation("tuner:finding", "f1", "r2", None)["payload"] == {
        "needs": "none"
    }


def test_check_sign_operation_corrects_with_signer_and_optional_note() -> None:
    assert check_sign_operation("tuner:check-run", "c1", "r3", "ann", "fine") == {
        "op": "correct",
        "type": "tuner:check-run",
        "id": "c1",
        "expected_revision": "r3",
        "payload": {"signed_by": "ann", "signed_note": "fine"},
    }
    assert check_sign_operation("tuner:check-run", "c1", "r3", "ann", None)["payload"] == {
        "signed_by": "ann"
    }


def test_plan_rejection_operation_creates_a_needs_human_finding() -> None:
    operation = plan_rejection_operation("plan-review:p one", " why ", "eff")
    assert operation["op"] == "create"
    assert operation["type"] == "tuner:finding"
    assert operation["subject"] == "plan-rejected:plan-review:p-one"
    assert operation["payload"] == {
        "claim": "Plan rejected for plan-review:p one; route to spec or tasks",
        "basis": "why",
        "needs": "human",
        "effort": "eff",
        "invalidated_when": "approach re-settled or tasks re-run",
    }
    assert str(operation["body"]).endswith("## Follow-up\n\nwhy")


def test_plan_rejection_operation_defaults_blank_note_and_caps_subject() -> None:
    operation = plan_rejection_operation("x" * 200, "  ", "eff")
    payload = operation["payload"]
    assert isinstance(payload, dict)
    assert payload["basis"] == "Rejected from dashboard Needs-you"
    assert len(str(operation["subject"])) == 120
