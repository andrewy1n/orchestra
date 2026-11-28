from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import make_project

from orchestra.canon.project import Project
from orchestra.cli import main
from orchestra.conductor.phases.workflow.workflow_review import record_step_review

EFFORT = "refunds-effort"
PHASE = "refunds"
SECTION = "## Applicable standing constraints"
RULE = "Only billing adapters may import the Stripe SDK."
BASIS = "Provider access belongs in billing adapters."
PHASE_BODY = (
    "## Problem\nSupport refunds.\n"
    "## Approach\nUse the payments API.\n"
    "## Exit criteria\nVerify the result.\n"
    "## Landing\nUse a phase worktree.\n"
)
SPEC_BODY = (
    "## Requirements\nR1: Refund a payment.\n"
    "## Acceptance criteria\nR1 passes.\n"
    "## Constraints\nKeep scope fixed.\n"
    "## Non-goals\nNo unrelated changes.\n"
    "## Invariants\nApproval remains explicit.\n"
    "## Assumptions\nThe store is available.\n"
)
DESIGN_BODY = (
    "## Architecture\nUse workflow records.\n"
    "## Interfaces\nUse typed APIs.\n"
    "## Decisions\nPersist reviews.\n"
    "## Invariants\nDo not infer approval.\n"
    "## Assumptions\nThe phase exists.\n"
    "## Tradeoffs\nKeep writes atomic.\n"
    "## Risks\nStale inputs need review.\n"
)


def _seed(root: Path) -> tuple[Project, str]:
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
        body=PHASE_BODY,
    )
    specification = project.create(
        record_type="score:specification",
        subject="refunds-spec",
        payload={"weight": "full", "phase": PHASE, "effort": EFFORT, "requirements": ["R1"]},
        body=SPEC_BODY,
    )
    record_step_review(
        project,
        phase=PHASE,
        step="spec",
        artifact=specification,
        authority="user-approval",
        basis="Approved.",
        source_reviews=[],
    )
    constraint = project.create(
        record_type="score:standing-constraint",
        subject="stripe-sdk-isolation",
        payload={
            "area": "payments",
            "rule": RULE,
            "check": "uv run pytest tests/architecture/test_stripe_imports.py",
        },
        body=f"## Basis\n\n{BASIS}\n",
    )
    return project, constraint["id"]


def _design_brief(root: Path, capsys: pytest.CaptureFixture[str], *areas: str) -> str:
    args = ["workflow", "brief", PHASE, "design", "--store", str(root)]
    for area in areas:
        args += ["--area", area]
    code = main(args)
    captured = capsys.readouterr()
    assert code == 0, captured.out + captured.err
    return captured.out


def test_naming_payments_for_refunds_surfaces_the_stripe_rule(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _, constraint_id = _seed(tmp_path)

    brief = _design_brief(tmp_path, capsys, "payments")

    assert SECTION in brief
    section = brief.split(SECTION, 1)[1]
    assert RULE in section
    assert BASIS in section
    assert constraint_id in section


def test_area_without_a_rule_names_no_rules(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project, _ = _seed(tmp_path)
    project.create(
        record_type="composer:area",
        subject="shipping",
        payload={"title": "Shipping"},
        body="## Scope\nShip items.",
    )

    brief = _design_brief(tmp_path, capsys, "shipping")

    assert "No standing constraints for area `shipping`." in brief
    assert RULE not in brief


def test_design_record_accepts_pinned_standing_constraints(tmp_path: Path) -> None:
    project, constraint_id = _seed(tmp_path)

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

    assert design["payload"]["standing_constraints"] == [constraint_id]


def test_missing_area_lists_the_areas_that_have_constraints(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _seed(tmp_path)

    brief = _design_brief(tmp_path, capsys)

    assert "No `--area` given" in brief
    assert "Areas with constraints: payments." in brief
    assert RULE not in brief
