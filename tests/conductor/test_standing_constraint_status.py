"""Standing constraint outcomes derive from check-runs at the revision under review."""

from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import make_project
from conductor_support import record_fixture_design_review

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.conductor.verification.standing_constraints import (
    criterion_id,
    standing_constraint_status,
)

EFFORT = "refunds-effort"
PHASE = "refunds"
NAME = "stripe-sdk-isolation"
CHECK = "uv run pytest tests/architecture/test_stripe_imports.py"
HEAD = "a" * 40
OTHER_HEAD = "b" * 40
OFFENDING = "orchestra/payments/refunds.py:3: import stripe"
DESIGN_BODY = (
    "## Architecture\nUse workflow records.\n"
    "## Interfaces\nUse typed APIs.\n"
    "## Decisions\nPersist reviews.\n"
    "## Invariants\nDo not infer approval.\n"
    "## Assumptions\nThe phase exists.\n"
    "## Tradeoffs\nKeep writes atomic.\n"
    "## Risks\nStale inputs need review.\n"
)


def _constraint_payload(rule: str) -> JsonObject:
    return {"area": "payments", "rule": rule, "check": CHECK}


def _seed(root: Path) -> tuple[Project, Record]:
    project = make_project(root)
    project.create(
        record_type="score:effort",
        subject=EFFORT,
        payload={"goal": "Refunds", "kind": "deliver"},
    )
    project.create(
        record_type="score:phase",
        subject=PHASE,
        payload={"title": PHASE, "ordinal": 1, "effort": EFFORT},
        body="## Problem\nRefunds.\n## Approach\nAPI.\n## Exit criteria\nDone.\n",
    )
    constraint = project.create(
        record_type="score:standing-constraint",
        subject=NAME,
        payload=_constraint_payload("Only billing adapters may import the Stripe SDK."),
        body="## Basis\n\nProvider access belongs in billing adapters.\n",
    )
    return project, constraint


def _pin(project: Project, constraint_id: str) -> Record:
    design = project.create(
        record_type="score:design",
        subject="refunds-design",
        payload={
            "phase": PHASE,
            "effort": EFFORT,
            "decisions": [],
            "standing_constraints": [constraint_id],
        },
        body=DESIGN_BODY,
    )

    record_fixture_design_review(project, design)
    return design


def _run(
    project: Project,
    constraint_id: str,
    result: str,
    *,
    revision: str = HEAD,
    body: str | None = None,
) -> Record:
    return project.create(
        record_type="tuner:check-run",
        subject=f"{NAME}-check",
        payload={
            "criterion_id": criterion_id(constraint_id),
            "revision": revision,
            "result": result,
            "effort": EFFORT,
            "method": "check",
            "runner": "orchestra",
            "signed_by": "",
        },
        body=body,
    )


def test_violated_constraint_reports_offending_import_while_feature_passes(
    tmp_path: Path,
) -> None:
    project, constraint = _seed(tmp_path)
    _pin(project, constraint["id"])
    feature = project.create(
        record_type="tuner:check-run",
        subject="refunds-feature",
        payload={
            "criterion_id": "refunds-feature",
            "revision": HEAD,
            "result": "pass",
            "effort": EFFORT,
            "method": "check",
            "runner": "orchestra",
            "signed_by": "",
        },
    )
    failed = _run(project, constraint["id"], "fail", body=f"{OFFENDING}\n")

    outcomes = standing_constraint_status(project.records(), PHASE, HEAD)

    assert feature["payload"]["result"] == "pass"
    assert len(outcomes) == 1
    assert outcomes[0].name == NAME
    assert outcomes[0].area == "payments"
    assert outcomes[0].pinned_id == constraint["id"]
    assert outcomes[0].outcome == "violated"
    assert outcomes[0].check_run_id == failed["id"]
    assert OFFENDING in outcomes[0].evidence
    assert outcomes[0].newer_id is None


def test_passing_check_run_at_head_verifies_constraint(tmp_path: Path) -> None:
    project, constraint = _seed(tmp_path)
    _pin(project, constraint["id"])
    passed = _run(project, constraint["id"], "pass")

    outcomes = standing_constraint_status(project.records(), PHASE, HEAD)

    assert [(o.outcome, o.check_run_id) for o in outcomes] == [("verified", passed["id"])]


def test_unverified_at_new_revision_even_though_earlier_revision_passed(tmp_path: Path) -> None:
    project, constraint = _seed(tmp_path)
    _pin(project, constraint["id"])
    _run(project, constraint["id"], "pass", revision=OTHER_HEAD)

    outcomes = standing_constraint_status(project.records(), PHASE, HEAD)

    assert [(o.pinned_id, o.outcome, o.check_run_id) for o in outcomes] == [
        (constraint["id"], "unverified", None)
    ]


def test_unverified_when_only_another_constraint_has_a_run(tmp_path: Path) -> None:
    project, constraint = _seed(tmp_path)
    _pin(project, constraint["id"])
    _run(project, "someone-else", "pass")

    outcomes = standing_constraint_status(project.records(), PHASE, HEAD)

    assert [o.outcome for o in outcomes] == ["unverified"]


def test_superseded_declaration_names_newer_and_old_pin_keeps_its_evidence(
    tmp_path: Path,
) -> None:
    project, old = _seed(tmp_path)
    _pin(project, old["id"])
    failed = _run(project, old["id"], "fail", body=f"{OFFENDING}\n")
    revised = project.supersede(
        old["id"],
        payload=_constraint_payload("Only payments/billing adapters may import the Stripe SDK."),
        body="## Basis\n\nProvider access belongs in billing adapters.\n",
    )["record"]

    outcomes = standing_constraint_status(project.records(), PHASE, HEAD)

    assert len(outcomes) == 1
    assert outcomes[0].pinned_id == old["id"]
    assert outcomes[0].newer_id == revised["id"]
    assert outcomes[0].outcome == "violated"
    assert outcomes[0].check_run_id == failed["id"]
    assert OFFENDING in outcomes[0].evidence


def test_pin_that_resolves_to_no_constraint_raises(tmp_path: Path) -> None:
    project, constraint = _seed(tmp_path)
    design = _pin(project, constraint["id"])
    broken: Record = {
        **design,
        "payload": {**design["payload"], "standing_constraints": ["<score:standing-constraint:x>"]},
    }
    records = [r for r in project.records() if r["id"] != design["id"]] + [broken]

    with pytest.raises(RecordShapeError, match="does not resolve to a standing constraint"):
        standing_constraint_status(records, PHASE, HEAD)


def test_no_head_reads_every_constraint_unverified(tmp_path: Path) -> None:
    project, constraint = _seed(tmp_path)
    _pin(project, constraint["id"])
    _run(project, constraint["id"], "pass")

    outcomes = standing_constraint_status(project.records(), PHASE, None)

    assert [(o.outcome, o.check_run_id) for o in outcomes] == [("unverified", None)]


@pytest.mark.parametrize("malformed", ["wrong-shape", [None]])
def test_malformed_approved_pins_raise(tmp_path: Path, malformed: JsonValue) -> None:
    project, constraint = _seed(tmp_path)
    design = _pin(project, constraint["id"])
    broken: Record = {
        **design,
        "payload": {**design["payload"], "standing_constraints": malformed},
    }
    records = [record for record in project.records() if record["id"] != design["id"]]
    with pytest.raises(RecordShapeError, match="must be a list of strings"):
        standing_constraint_status([*records, broken], PHASE, HEAD)
