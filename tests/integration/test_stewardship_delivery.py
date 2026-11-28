from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import seed_effort
from interfaces.interfaces_support import invoke

from integration.test_architecture_change_review import orchestra_output, reconcile_stripe_adapter
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.score.planning.standing_constraint import is_current_constraint
from orchestra.tools import Git

EFFORT = "merchant-refunds"
PHASE = "refunds"
SPEC = """## Requirements

R1: Deliver refunds.

## Acceptance criteria

Refunds succeed.

## Constraints

Respect the payments boundary.

## Non-goals

Shipping.

## Invariants

Keep Stripe behind the adapter.

## Assumptions

The Stripe adapter is available.
"""
DESIGN = """## Architecture

Call the Stripe adapter through billing.

## Interfaces

Use the payments API.

## Decisions

Use the accepted payment-provider decision.

## Invariants

Only the Stripe adapter may import the SDK.

## Assumptions

The updated standing rule is active.

## Tradeoffs

Billing owns provider integration.

## Risks

A refund implementation may import the provider directly.
"""


def _billing_context(project: Project) -> None:
    for area, title in (("payments", "Capture card payments"), ("shipping", "Buy labels")):
        project.create(
            record_type="composer:area",
            subject=area,
            payload={"title": area.title()},
            body=f"## Scope\nOwn {area}.",
        )
        project.create(
            record_type="composer:product-item",
            subject=f"{area}-capability",
            payload={"title": title, "description": title, "status": "current", "area": area},
        )
    project.create(
        record_type="composer:product",
        subject="product",
        payload={"purpose": "Manage merchant payments.", "audience": "Marketplace operators."},
    )
    project.create(
        record_type="composer:component",
        subject="shipping",
        payload={"area": "shipping"},
        body="## Responsibility\nBuy labels and quote freight.",
    )
    project.create(
        record_type="composer:interface",
        subject="payments-api",
        payload={"connects": ["payments"]},
        body="## Provides\nSubmit refunds.",
    )


def _review_step(project: Project, step: str, record: Record) -> None:
    orchestra_output(
        project.project_root,
        "workflow",
        "review",
        PHASE,
        step,
        "--artifact",
        record["id"],
        "--authority",
        "user-approval",
        "--basis",
        "Approved for the refunds scenario.",
    )


@pytest.fixture
def refunds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Project, str]:
    project = reconcile_stripe_adapter(tmp_path, monkeypatch)
    _billing_context(project)
    seed_effort(project, EFFORT, PHASE)
    (current,) = (
        constraint
        for constraint in project.list("score:standing-constraint")
        if constraint["subject"] == "imports" and is_current_constraint(constraint)
    )
    return project, current["id"]


def _open_design(project: Project) -> str:
    specification = project.create(
        record_type="score:specification",
        subject=PHASE,
        payload={"weight": "full", "phase": PHASE, "effort": EFFORT, "requirements": ["R1"]},
        body=SPEC,
    )
    _review_step(project, "spec", specification)
    return orchestra_output(
        project.project_root, "workflow", "brief", PHASE, "design", "--area", "payments"
    )


def test_later_phase_receives_reconciled_context(refunds: tuple[Project, str]) -> None:
    project, pinned = refunds

    spec = orchestra_output(
        project.project_root, "workflow", "brief", PHASE, "spec", "--area", "payments"
    )
    assert "Manage merchant payments." in spec
    assert "Marketplace operators." in spec
    assert "Capture card payments" in spec
    assert "Buy labels" not in spec

    design = _open_design(project)
    assert "Own payments." in design
    assert "payments-api" in design
    assert "Adopt the Stripe adapter." in design
    assert "Allow imports of the Stripe adapter." in design
    assert pinned in design
    assert "Use the original payment provider." not in design
    assert "Disallow Stripe imports." not in design
    assert "quote freight" not in design


def test_review_reports_revision_specific_pinned_outcomes(refunds: tuple[Project, str]) -> None:
    project, pinned = refunds
    root = project.project_root
    assert pinned in _open_design(project)
    design = project.create(
        record_type="score:design",
        subject=PHASE,
        payload={
            "phase": PHASE,
            "effort": EFFORT,
            "decisions": [],
            "standing_constraints": [pinned],
        },
        body=DESIGN,
    )
    _review_step(project, "design", design)
    newer = project.supersede(
        pinned, payload={"rule": "A later phase may import Stripe.", "check": "true"}
    )["record"]
    acceptance = project.create(
        record_type="score:acceptance",
        subject="refunds-behavior",
        payload={
            "phase": PHASE,
            "effort": EFFORT,
            "requirement": "R1",
            "method": "check",
            "verify_command": "grep -qx 'refund = 10' refunds.py",
        },
    )

    git = Git(root)
    git.text("switch", "-c", f"phase/{PHASE}")
    (root / "refunds.py").write_text("import stripe\nrefund = 10\n", encoding="utf-8")
    git.text("add", "refunds.py")
    git.text("commit", "-qm", "Implement refunds with a direct Stripe import")
    reviewed = git.head()
    orchestra_output(root, "check", "--acceptance", acceptance["id"])
    result = invoke(
        "orchestra", ["check", "--phase", PHASE, "--standing-constraint", "imports"], root
    )
    assert result.code == 1, result.err
    assert "import stripe" in result.out

    view = orchestra_output(root, "view", "verification", "--effort", EFFORT)
    assert "**R1**: verified" in view
    rule = next(line for line in view.splitlines() if "**imports**" in line)
    assert "violated" in rule
    assert pinned in rule and reviewed[:7] in rule
    assert newer["id"] in rule

    (root / "refunds.py").write_text("import stripe_adapter\nrefund = 10\n", encoding="utf-8")
    git.text("add", "refunds.py")
    git.text("commit", "-qm", "Use the Stripe adapter")
    fresh = git.head()
    view = orchestra_output(root, "view", "verification", "--effort", EFFORT)
    rule = next(line for line in view.splitlines() if "**imports**" in line)
    assert "unverified" in rule
    assert pinned in rule and fresh[:7] in rule
