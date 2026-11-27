from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import make_project, seed_effort

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.composer.architecture_change import proposal_for_phase


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    seed_effort(project, effort="payments", phase="stripe")
    project.create(
        record_type="composer:component",
        subject="gateway",
        payload={"area": "payments"},
        body="## Responsibility\nProcess payments.",
    )
    return project


def _proposal(project: Project, **fields: JsonValue) -> Record:
    payload: JsonObject = {
        "phase": "stripe",
        "status": "pending",
        "adr": "provider",
        "affects": ["gateway"],
    }
    payload.update(fields)
    return project.create(
        record_type="composer:architecture-proposal",
        subject="stripe",
        payload=payload,
        body="## Rationale\nAuthorize the Stripe adapter.",
    )


def test_adr_proposal_pins_merged_decision_and_keeps_withdrawal_history(project: Project) -> None:
    adr = project.create(
        record_type="composer:architecture-decision",
        subject="provider",
        payload={"status": "accepted", "affects": ["gateway"]},
        body="## Rationale\nUse the original provider.",
    )
    proposed = _proposal(project, base_adr=adr["id"], base_adr_revision=adr["revision"])
    result = proposal_for_phase(project.records(), "stripe")
    assert result is not None
    assert result.adr == "provider"
    assert result.affects == ("gateway",)
    assert result.rationale == "Authorize the Stripe adapter."
    assert result.base_adr is not None
    assert (result.base_adr.id, result.base_adr.revision) == (adr["id"], adr["revision"])
    withdrawn = project.supersede(proposed["id"], payload={"status": "withdrawn"})["record"]
    result = proposal_for_phase(project.records(), "stripe")
    assert result is not None
    assert result.status == "withdrawn"
    assert result.record["id"] == withdrawn["id"]
    assert project.get(proposed["id"])["payload"]["status"] == "pending"
    assert project.get(adr["id"])["revision"] == adr["revision"]


def test_constraint_operations_pin_add_revision_and_retirement(project: Project) -> None:
    changes: list[str] = []
    for operation, subject in [("add", "imports"), ("revise", "legacy"), ("retire", "obsolete")]:
        payload: JsonObject = {"operation": operation, "constraint": subject}
        if operation != "add":
            baseline = project.create(
                record_type="score:standing-constraint",
                subject=subject,
                payload={"area": "payments", "rule": "Forbid imports.", "check": "check-imports"},
                body="## Basis\nIsolate vendors.",
            )
            payload.update(
                base_constraint=baseline["id"], base_constraint_revision=baseline["revision"]
            )
        if operation != "retire":
            payload.update(
                area="payments",
                rule="Allow the Stripe adapter.",
                check="check-imports",
                targets=["gateway"],
            )
        record = project.create(
            record_type="composer:constraint-change",
            subject=subject,
            payload=payload,
            body="## Basis\nKeep payment integrations isolated.",
        )
        changes.append(record["id"])
    _proposal(project, constraints=[*changes])
    result = proposal_for_phase(project.records(), "stripe")
    assert result is not None
    assert [(change.operation, change.subject) for change in result.constraints] == [
        ("add", "imports"),
        ("revise", "legacy"),
        ("retire", "obsolete"),
    ]
    assert result.constraints[0].base is None
    assert result.constraints[1].base is not None
    assert result.constraints[2].payload == {}
    assert result.constraints[0].payload["targets"] == ["gateway"]
    assert len(project.list("score:standing-constraint")) == 2
