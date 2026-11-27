from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from canon_support import make_project, seed_effort
from interfaces.interfaces_support import invoke

from orchestra.canon.project import Project
from orchestra.canon.types import JsonValue, Record
from orchestra.composer.architecture import current_architecture
from orchestra.conductor.cli import close as close_cli
from orchestra.tools import Git


@dataclass
class PullRequest:
    head: str
    state: str = "OPEN"

    def pull_request_state(self, number: int) -> tuple[str, str]:
        assert number == 7
        return self.state, self.head


@dataclass
class Change:
    project: Project
    pull_request: PullRequest
    baseline: Record
    proposal: Record


@pytest.fixture
def change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Change:
    project = make_project(tmp_path)
    seed_effort(project, "payments", "stripe")
    project.create(
        record_type="composer:component",
        subject="gateway",
        payload={"area": "payments"},
        body="## Responsibility\nProcess payments.",
    )
    baseline = project.create(
        record_type="score:standing-constraint",
        subject="imports",
        payload={
            "area": "payments",
            "rule": "Use the current adapter.",
            "check": "true",
            "targets": ["gateway"],
        },
        body="## Basis\nKeep integration isolated.",
    )
    choice = project.create(
        record_type="composer:architecture-decision",
        subject="processor",
        payload={"status": "accepted", "affects": ["gateway"], "enforced_by": ["imports"]},
        body="## Rationale\nUse the original processor.",
    )
    proposed_rule = project.create(
        record_type="composer:constraint-change",
        subject="stripe-imports",
        payload={
            "operation": "revise",
            "constraint": "imports",
            "base_constraint": baseline["id"],
            "base_constraint_revision": baseline["revision"],
            "area": "payments",
            "rule": "Allow the Stripe adapter.",
            "check": "true",
            "targets": ["gateway"],
        },
        body="## Basis\nKeep integration isolated.",
    )
    proposal = project.create(
        record_type="composer:architecture-proposal",
        subject="stripe",
        payload={
            "phase": "stripe",
            "status": "pending",
            "adr": "processor",
            "base_adr": choice["id"],
            "base_adr_revision": choice["revision"],
            "affects": ["gateway"],
            "enforced_by": ["imports"],
            "constraints": [proposed_rule["id"]],
        },
        body="## Rationale\nAdopt Stripe.",
    )
    git = Git(tmp_path)
    head = git.head()
    project.create(
        record_type="conductor:landing",
        subject="stripe",
        payload={
            "phase": "stripe",
            "number": 7,
            "url": "https://example.com/pr/7",
            "head_sha": head,
            "result": "success",
        },
    )
    project.create(
        record_type="composer:architecture-approval",
        subject="stripe",
        payload={
            "proposal": proposal["id"],
            "proposal_revision": proposal["revision"],
            "candidate": head,
            "approved_by": "maintainer",
        },
    )
    pull_request = PullRequest(head)
    monkeypatch.setattr(close_cli, "github_client", lambda _repo: pull_request)
    return Change(project, pull_request, baseline, proposal)


def test_applies_both_changes_after_merge_and_retry_is_idempotent(change: Change) -> None:
    project = change.project
    root = project.project_root
    result = invoke("orchestra", ["close", "--phase", "stripe"], root)
    assert result.code == 0, result.err
    assert project.resolve("score:standing-constraint", "imports")["id"] == change.baseline["id"]

    change.pull_request.state = "MERGED"
    result = invoke("orchestra", ["close", "--phase", "stripe"], root)
    assert result.code == 0, result.err
    model = current_architecture(project.records())
    assert model.areas["payments"][0].decisions[0].rationale == "Adopt Stripe."
    updated = model.constraints["imports"]
    assert updated["payload"]["rule"] == "Allow the Stripe adapter."
    assert project.get(change.baseline["id"])["payload"]["rule"] == "Use the current adapter."
    result = invoke("orchestra", ["close", "--phase", "stripe"], root)
    assert result.code == 0, result.err
    assert project.resolve("score:standing-constraint", "imports")["id"] == updated["id"]
    assert len(project.list("composer:architecture-decision")) == 2


def test_changed_baseline_refuses_the_entire_proposal(change: Change) -> None:
    project = change.project
    project.supersede(change.baseline["id"], payload={"rule": "A different change landed."})
    change.pull_request.state = "MERGED"
    result = invoke("orchestra", ["close", "--phase", "stripe"], project.project_root)
    assert result.code != 0
    assert "requires refreshed review" in result.err
    assert len(project.list("composer:architecture-decision")) == 1
    assert project.resolve("score:phase", "stripe")["lifecycle_state"] == "planned"


def _approve_revision(change: Change, **payload: JsonValue) -> None:
    project = change.project
    revision = project.supersede(change.proposal["id"], payload=payload)["record"]
    project.create(
        record_type="composer:architecture-approval",
        subject="stripe",
        payload={
            "proposal": revision["id"],
            "proposal_revision": revision["revision"],
            "candidate": change.pull_request.head,
            "approved_by": "maintainer",
        },
    )


def test_retired_constraint_is_removed_from_current_model_but_the_pin_resolves(
    change: Change,
) -> None:
    project = change.project
    retirement = project.create(
        record_type="composer:constraint-change",
        subject="retire-imports",
        payload={
            "operation": "retire",
            "constraint": "imports",
            "base_constraint": change.baseline["id"],
            "base_constraint_revision": change.baseline["revision"],
        },
        body="## Basis\nReplace the old import strategy.",
    )
    _approve_revision(change, enforced_by=[], constraints=[retirement["id"]])
    change.pull_request.state = "MERGED"
    result = invoke("orchestra", ["close", "--phase", "stripe"], project.project_root)
    assert result.code == 0, result.err
    model = current_architecture(project.records())
    assert model.constraints == {}
    assert model.areas["payments"][0].constraints == ()
    assert project.get(change.baseline["id"])["payload"]["rule"] == "Use the current adapter."


def test_failed_write_rolls_back_earlier_constraint_revision(change: Change) -> None:
    project = change.project
    invalid = project.create(
        record_type="composer:constraint-change",
        subject="invalid-change",
        payload={
            "operation": "add",
            "constraint": "invalid constraint subject",
            "area": "payments",
            "rule": "Allow valid imports.",
            "check": "true",
        },
        body="## Basis\nIsolate integrations.",
    )
    current_changes = change.proposal["payload"]["constraints"]
    assert isinstance(current_changes, list)
    _approve_revision(change, constraints=[*current_changes, invalid["id"]])
    change.pull_request.state = "MERGED"
    result = invoke("orchestra", ["close", "--phase", "stripe"], project.project_root)
    assert result.code != 0
    assert "subject must be a non-empty slug" in result.err
    assert project.resolve("score:standing-constraint", "imports")["id"] == change.baseline["id"]
    assert project.list("composer:architecture-reconciliation") == []
