from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import make_project, seed_effort
from interfaces.interfaces_support import invoke

from orchestra.canon.project import open_store
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
            "enforced_by": ["stripe-imports"],
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


def test_candidate_evidence_refuses_changes_during_the_check(
    candidate: tuple[Path, str, str, Record],
) -> None:
    root, base, head, rule = candidate
    project = open_store(root)
    updated_rule = project.correct(rule["id"], payload={"check": "touch check-output.txt"})[
        "record"
    ]
    proposal = project.resolve("composer:architecture-proposal", "stripe")
    project.supersede(proposal["id"], payload={"constraints": [updated_rule["id"]]})
    check = invoke(
        "orchestra",
        ["check", "--proposed-constraint", updated_rule["id"], "--phase", "stripe"],
        root,
    )
    assert check.code == 3
    assert "changed during the proposed constraint check" in check.err
    assert project.list("tuner:check-run") == []
    assert "stripe-imports: unverified" in _review(root, base, head)


def test_review_shows_material_fields(
    candidate: tuple[Path, str, str, Record],
) -> None:
    root, base, head, _ = candidate
    brief = _review(root, base, head)
    assert "ADR enforcement rules stripe-imports" in brief
    assert "Area payments" in brief
    assert "Targets gateway" in brief
    assert "Check command" in brief
    assert "        true" in brief


def test_dependency_changes_keep_src_package_when_declared(
    candidate: tuple[Path, str, str, Record],
) -> None:
    root, _, base, _ = candidate
    project = open_store(root)
    for component, prefix in (("gateway", "src.payments"), ("adapter", "src.stripe_adapter")):
        current = project.resolve("composer:component", component)
        project.supersede(current["id"], payload={"module_prefixes": [prefix]})
    package = root / "src"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "payments.py").write_text("from . import stripe_adapter\n")
    (package / "stripe_adapter.py").write_text("")
    git = Git(root)
    git.text("add", "src")
    git.text("commit", "-qm", "Add a dependency inside the src package")
    assert "Added: gateway → adapter" in _review(root, base, git.head())


def test_candidate_evidence_refuses_hidden_untracked_files(
    candidate: tuple[Path, str, str, Record],
) -> None:
    root, _, _, rule = candidate
    project = open_store(root)
    updated_rule = project.correct(rule["id"], payload={"check": "test -f local.txt"})["record"]
    proposal = project.resolve("composer:architecture-proposal", "stripe")
    project.supersede(proposal["id"], payload={"constraints": [updated_rule["id"]]})
    (root / "local.txt").write_text("Ignore me in status output.\n")
    Git(root).text("config", "status.showUntrackedFiles", "no")
    check = invoke(
        "orchestra",
        ["check", "--proposed-constraint", updated_rule["id"], "--phase", "stripe"],
        root,
    )
    assert check.code == 3
    assert "requires a clean candidate worktree" in check.err
    assert project.list("tuner:check-run") == []


@pytest.mark.parametrize("revision", [None, "sha256:older-rule"])
def test_candidate_evidence_ignores_mismatched_provenance(
    candidate: tuple[Path, str, str, Record], revision: str | None
) -> None:
    root, base, head, rule = candidate
    project = open_store(root)
    project.create(
        record_type="tuner:check-run",
        subject="stripe-imports-check",
        payload={
            "criterion_id": f"standing-constraint:{rule['id']}",
            "revision": head,
            "result": "pass",
            "effort": "payments",
            "method": "check",
            "signed_by": "",
            "runner": "orchestra",
        },
        provenance={"acceptance_revision": revision} if revision is not None else None,
    )
    assert "stripe-imports: unverified" in _review(root, base, head)
