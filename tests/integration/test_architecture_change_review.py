from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from canon_support import make_project, seed_effort
from interfaces.interfaces_support import invoke

from orchestra.canon.project import Project
from orchestra.conductor.cli import close as close_cli
from orchestra.tools import Git


@dataclass
class MergedPullRequest:
    candidate: str

    def pull_request_state(self, number: int) -> tuple[str, str]:
        assert number == 9
        return "MERGED", self.candidate


def orchestra_output(path: Path, *args: str) -> str:
    result = invoke("orchestra", list(args), path)
    assert result.code == 0, result.err
    return result.out


def reconcile_stripe_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, withdraw: bool = False
) -> Project:
    project = make_project(tmp_path)
    seed_effort(project, "payments", "stripe")
    (tmp_path / ".git" / "info" / "exclude").write_text(".canon/\n", encoding="utf-8")
    for name, prefix in (("payments", "payments"), ("stripe-adapter", "stripe_adapter")):
        project.create(
            record_type="composer:component",
            subject=name,
            payload={"area": "payments", "module_prefixes": [prefix]},
            body=f"## Responsibility\nOwn {prefix}.",
        )
    adr = project.create(
        record_type="composer:architecture-decision",
        subject="payment-provider",
        payload={"status": "accepted", "affects": ["payments"], "enforced_by": ["imports"]},
        body="## Rationale\nUse the original payment provider.",
    )
    baseline = project.create(
        record_type="score:standing-constraint",
        subject="imports",
        payload={"area": "payments", "rule": "Disallow Stripe imports.", "check": "true"},
        body="## Basis\nKeep vendors isolated.",
    )
    rule = project.create(
        record_type="composer:constraint-change",
        subject="stripe-imports",
        payload={
            "operation": "revise",
            "constraint": "imports",
            "base_constraint": baseline["id"],
            "base_constraint_revision": baseline["revision"],
            "area": "payments",
            "rule": "Allow imports of the Stripe adapter.",
            "check": "! grep -x 'import stripe' *.py",
        },
        body="## Basis\nIsolate Stripe behind the adapter.",
    )
    proposal = project.create(
        record_type="composer:architecture-proposal",
        subject="stripe",
        payload={
            "phase": "stripe",
            "status": "pending",
            "adr": "payment-provider",
            "affects": ["payments", "stripe-adapter"],
            "enforced_by": ["imports"],
            "base_adr": adr["id"],
            "base_adr_revision": adr["revision"],
            "constraints": [rule["id"]],
        },
        body="## Rationale\nAdopt the Stripe adapter.",
    )
    git = Git(tmp_path)
    git.text("branch", "-M", "main")
    git.text("switch", "-c", "phase/stripe")
    (tmp_path / "payments.py").write_text("import stripe_adapter\n", encoding="utf-8")
    (tmp_path / "stripe_adapter.py").write_text("", encoding="utf-8")
    git.text("add", "payments.py", "stripe_adapter.py")
    git.text("commit", "-qm", "Add a Stripe adapter")
    candidate = git.head()

    architecture_args = ("view", "architecture", "--component", "payments")
    before = orchestra_output(tmp_path, *architecture_args)
    assert "Use the original payment provider." in before
    assert "Disallow Stripe imports." in before

    review_args = ("review-brief", "--phase", "stripe", "--phase-head", candidate)
    assert "imports: unverified" in orchestra_output(tmp_path, *review_args)
    orchestra_output(tmp_path, "check", "--phase", "stripe", "--proposed-constraint", rule["id"])
    review = orchestra_output(tmp_path, *review_args)
    assert "Adopt the Stripe adapter." in review
    assert "Added: payments → stripe-adapter" in review
    assert "imports: verified" in review

    project.create(
        record_type="composer:architecture-approval",
        subject="stripe",
        payload={
            "proposal": proposal["id"],
            "proposal_revision": proposal["revision"],
            "candidate": candidate,
            "approved_by": "maintainer",
        },
    )
    if withdraw:
        project.supersede(proposal["id"], payload={"status": "withdrawn"})
        assert "(withdrawn)" in orchestra_output(tmp_path, *review_args)
        assert "Use the original payment provider." in orchestra_output(
            tmp_path, *architecture_args
        )

    git.text("switch", "main")
    git.text("merge", "--squash", "phase/stripe")
    git.text("commit", "-qm", "Merge the Stripe phase")
    assert git.head() != candidate
    project.create(
        record_type="conductor:landing",
        subject="stripe",
        payload={
            "phase": "stripe",
            "number": 9,
            "url": "https://example.com/pr/9",
            "head_sha": candidate,
            "result": "success",
        },
    )
    monkeypatch.setattr(close_cli, "github_client", lambda _repo: MergedPullRequest(candidate))
    orchestra_output(tmp_path, "close", "--phase", "stripe")
    after = orchestra_output(tmp_path, *architecture_args)
    if withdraw:
        assert "Use the original payment provider." in after
        assert "Disallow Stripe imports." in after
        assert project.list("composer:architecture-reconciliation") == []
    else:
        assert "Adopt the Stripe adapter." in after
        assert "Allow imports of the Stripe adapter." in after
        assert "outcome: unverified" in after
        assert len(project.list("composer:architecture-reconciliation")) == 1

    (evidence,) = project.list("tuner:check-run")
    assert evidence["payload"]["revision"] == candidate
    assert evidence["payload"]["criterion_id"] == f"standing-constraint:{rule['id']}"
    return project


@pytest.mark.parametrize("withdraw", [False, True])
def test_payments_proposal_through_review_and_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, withdraw: bool
) -> None:
    reconcile_stripe_adapter(tmp_path, monkeypatch, withdraw=withdraw)
