from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import make_project

from orchestra.canon.project import Project
from orchestra.cli import main
from orchestra.conductor.phases.workflow.workflow_review import record_step_review

EFFORT = "refunds-effort"
PHASE = "refunds"


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = make_project(tmp_path)
    project.create(
        record_type="score:effort",
        subject=EFFORT,
        payload={"goal": "Support refunds", "kind": "deliver"},
    )
    project.create(
        record_type="score:phase",
        subject=PHASE,
        payload={"title": "Refunds", "effort": EFFORT, "ordinal": 1},
        body="## Problem\nSupport refunds.\n## Approach\nUse billing.\n## Exit criteria\nRefund a payment.",
    )
    return project


def test_spec_brief_shows_scoped_product_context(
    project: Project, capsys: pytest.CaptureFixture[str]
) -> None:
    project.create(
        record_type="composer:product",
        subject="product",
        payload={"purpose": "Manage merchant payments.", "audience": "Marketplace operators."},
    )
    for area, title in (("billing", "Capture card payments"), ("shipping", "Buy shipping labels")):
        project.create(
            record_type="composer:area",
            subject=area,
            payload={"title": area.title()},
            body=f"## Scope\nOwn {area}.",
        )
        project.create(
            record_type="composer:product-item",
            subject=f"{area}-capability",
            payload={
                "title": title,
                "description": f"Available in {area}.",
                "status": "current",
                "area": area,
            },
        )

    code = main(
        [
            "workflow",
            "brief",
            PHASE,
            "spec",
            "--area",
            "billing",
            "--store",
            str(project.project_root),
        ]
    )
    result = capsys.readouterr()

    assert code == 0, result.out + result.err
    assert "Manage merchant payments." in result.out
    assert "Marketplace operators." in result.out
    assert "Capture card payments" in result.out
    assert "Buy shipping labels" not in result.out


@pytest.mark.parametrize(
    ("flag", "scope"),
    [("--area", "billing"), ("--component", "billing-adapter"), ("--interface", "refund-api")],
)
def test_design_brief_shows_scoped_architecture_context(
    project: Project, capsys: pytest.CaptureFixture[str], flag: str, scope: str
) -> None:
    spec = project.create(
        record_type="score:specification",
        subject=PHASE,
        payload={"weight": "full", "phase": PHASE, "effort": EFFORT, "requirements": ["R1"]},
        body=(
            "## Requirements\nR1: Refund a payment.\n"
            "## Acceptance criteria\nR1 passes.\n"
            "## Constraints\nNone.\n## Non-goals\nNone.\n"
            "## Invariants\nNone.\n## Assumptions\nNone.\n"
        ),
    )
    record_step_review(
        project,
        phase=PHASE,
        step="spec",
        artifact=spec,
        authority="user-approval",
        basis="Approved.",
    )
    for area, responsibility in (
        ("billing", "Owns card refunds."),
        ("shipping", "Quotes freight."),
    ):
        project.create(
            record_type="composer:component",
            subject=f"{area}-adapter",
            payload={"area": area},
            body=f"## Responsibility\n{responsibility}",
        )
    project.create(
        record_type="composer:interface",
        subject="refund-api",
        payload={"connects": ["billing-adapter"]},
        body="## Provides\nSubmit a refund.",
    )
    project.create(
        record_type="composer:architecture-decision",
        subject="isolate-stripe",
        payload={"status": "accepted", "affects": ["billing-adapter", "refund-api"]},
        body="## Rationale\nKeep the payment provider replaceable.",
    )
    rule = project.create(
        record_type="score:standing-constraint",
        subject="stripe-isolation",
        payload={
            "area": "billing",
            "rule": "Only billing adapters import Stripe.",
            "check": "true",
            "targets": ["billing-adapter", "refund-api"],
        },
        body="## Basis\nKeep Stripe behind the adapter.",
    )

    code = main(
        [
            "workflow",
            "brief",
            PHASE,
            "design",
            flag,
            scope,
            "--store",
            str(project.project_root),
        ]
    )
    result = capsys.readouterr()

    assert code == 0, result.out + result.err
    assert f"## Architecture context for {flag[2:]} {scope}" in result.out
    if flag != "--interface":
        assert "Owns card refunds." in result.out
    assert "Submit a refund." in result.out
    assert "refund-api" in result.out
    assert "Keep the payment provider replaceable." in result.out
    assert "Only billing adapters import Stripe." in result.out
    assert rule["id"] in result.out
    assert "Quotes freight." not in result.out
