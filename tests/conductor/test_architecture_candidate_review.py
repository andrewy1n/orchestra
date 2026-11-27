from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import make_project, seed_effort
from interfaces.interfaces_support import invoke

from orchestra.canon.types import Record
from orchestra.tools import Git


@pytest.fixture
def candidate(tmp_path: Path) -> tuple[Path, str, str, Record]:
    project = make_project(tmp_path)
    seed_effort(project, "payments", "stripe")
    for component, package in (("gateway", "payments"), ("adapter", "stripe_adapter")):
        project.create(
            record_type="composer:component",
            subject=component,
            payload={"area": "payments", "module_prefixes": [package]},
            body=f"## Responsibility\nOwn {package}.",
        )
    rule = project.create(
        record_type="composer:constraint-change",
        subject="stripe-imports",
        payload={
            "operation": "add",
            "constraint": "stripe-imports",
            "area": "payments",
            "rule": "Allow the Stripe adapter.",
            "check": "true",
            "targets": ["gateway"],
        },
        body="## Basis\nAuthorize vendor imports.",
    )
    project.create(
        record_type="composer:architecture-proposal",
        subject="stripe",
        payload={
            "phase": "stripe",
            "status": "pending",
            "adr": "stripe-adr",
            "affects": ["gateway", "adapter"],
            "constraints": [rule["id"]],
        },
        body="## Rationale\nAuthorize the Stripe adapter.",
    )
    (tmp_path / ".git" / "info" / "exclude").write_text(".canon/\n")
    git = Git(tmp_path)
    git.text("branch", "-M", "main")
    baseline = git.head()
    git.text("switch", "-c", "candidate")
    (tmp_path / "payments.py").write_text("import stripe_adapter\nimport unknown_vendor\n")
    (tmp_path / "stripe_adapter.py").write_text("")
    git.text("add", "payments.py", "stripe_adapter.py")
    git.text("commit", "-qm", "Add adapter dependencies")
    return tmp_path, baseline, git.head(), rule


def _review(root: Path, base: str, head: str) -> str:
    result = invoke(
        "orchestra",
        ["review-brief", "--phase", "stripe", "--base", base, "--phase-head", head],
        root,
    )
    assert result.code == 0, result.err
    return result.out


def test_dependency_changes_are_shown_beside_proposal(
    candidate: tuple[Path, str, str, Record],
) -> None:
    root, base, head, _ = candidate
    brief = _review(root, base, head)
    assert "## Proposed architecture changes" in brief
    assert "Authorize the Stripe adapter." in brief
    assert "Added: gateway → adapter" in brief
    assert "Added: gateway → unresolved module unknown_vendor" in brief


def test_candidate_evidence_matches_rule_and_commit(
    candidate: tuple[Path, str, str, Record],
) -> None:
    root, base, head, rule = candidate
    assert "stripe-imports: unverified" in _review(root, base, head)
    check = invoke(
        "orchestra",
        ["check", "--proposed-constraint", rule["id"], "--phase", "stripe"],
        root,
    )
    assert check.code == 0, check.err
    assert "stripe-imports: verified" in _review(root, base, head)
    git = Git(root)
    git.text("commit", "--allow-empty", "-qm", "Different candidate")
    assert "stripe-imports: unverified" in _review(root, base, git.head())
