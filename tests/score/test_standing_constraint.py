from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject
from orchestra.score.planning.standing_constraint import StandingConstraint, applicable

NAME = "stripe-sdk-isolation"
CHECK = "uv run pytest tests/architecture/test_stripe_imports.py"
FIRST_RULE = "Only billing adapters may import the Stripe SDK."
REVISED_RULE = "Only billing adapters under payments/billing may import the Stripe SDK."
BASIS = "Provider access belongs in billing adapters so payments code stays provider-neutral."


@pytest.fixture()
def project(store_template: Path, tmp_path: Path) -> Project:
    root = tmp_path / "repo"
    shutil.copytree(store_template, root)
    return open_store(root)


def _payload(rule: str) -> JsonObject:
    return {"area": "payments", "rule": rule, "check": CHECK}


def test_applicable_returns_only_current_declaration_for_area(project: Project) -> None:
    declared = project.create(
        record_type="score:standing-constraint",
        subject=NAME,
        payload=_payload(FIRST_RULE),
        body=f"## Basis\n\n{BASIS}\n",
    )
    revised = project.supersede(
        declared["id"],
        payload=_payload(REVISED_RULE),
        body=f"## Basis\n\n{BASIS}\n",
    )["record"]

    assert applicable(project.records(), "payments") == [
        StandingConstraint(
            id=revised["id"],
            name=NAME,
            area="payments",
            rule=REVISED_RULE,
            check=CHECK,
            basis=BASIS,
        )
    ]
    assert applicable(project.records(), "search") == []
