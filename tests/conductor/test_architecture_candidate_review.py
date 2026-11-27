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
    (tmp_path / "helpers.py").write_text("")
    git.text("add", "payments.py", "stripe_adapter.py", "helpers.py")
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
    assert "Unmapped first-party modules helpers" in brief
    assert "unknown_vendor" not in brief.split("## Observed component dependency changes", 1)[1]


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


@pytest.mark.parametrize("mask", ["sparse", "assume-unchanged", "skip-worktree"])
def test_candidate_evidence_refuses_an_incomplete_checkout(
    candidate: tuple[Path, str, str, Record], mask: str
) -> None:
    root, _, _, rule = candidate
    project = open_store(root)
    git = Git(root)
    if mask == "sparse":
        git.text("sparse-checkout", "set", "--no-cone", "/payments.py")
        assert not (root / "stripe_adapter.py").exists()
        command = "test ! -e stripe_adapter.py"
    else:
        git.text("update-index", f"--{mask}", "--", "stripe_adapter.py")
        (root / "stripe_adapter.py").write_text("allowed\n")
        command = "grep -qx allowed stripe_adapter.py"
    assert git.status_porcelain() == ""
    updated_rule = project.correct(rule["id"], payload={"check": command})["record"]
    proposal = project.resolve("composer:architecture-proposal", "stripe")
    project.supersede(proposal["id"], payload={"constraints": [updated_rule["id"]]})
    check = invoke(
        "orchestra",
        ["check", "--proposed-constraint", updated_rule["id"], "--phase", "stripe"],
        root,
    )
    assert check.code == 3
    assert "requires a complete candidate checkout" in check.err
    assert project.list("tuner:check-run") == []


def test_duplicate_module_prefix_refuses_review(candidate: tuple[Path, str, str, Record]) -> None:
    root, base, head, _ = candidate
    project = open_store(root)
    adapter = project.resolve("composer:component", "adapter")
    project.supersede(adapter["id"], payload={"module_prefixes": ["payments"]})
    result = invoke(
        "orchestra",
        ["review-brief", "--phase", "stripe", "--base", base, "--phase-head", head],
        root,
    )
    assert result.code != 0
    assert "Multiple components declare module prefix 'payments'" in result.err


@pytest.mark.parametrize("source", ["def broken(\n", "from ... import unknown\n"])
def test_mapped_source_parse_or_import_failure_is_reported(
    candidate: tuple[Path, str, str, Record], source: str
) -> None:
    root, _, base, _ = candidate
    git = Git(root)
    (root / "payments.py").write_text(source)
    git.text("add", "payments.py")
    git.text("commit", "-qm", "Add invalid mapped source")
    result = invoke("orchestra", ["review-brief", "--phase", "stripe", "--base", base], root)
    assert result.code != 0
    assert f"Cannot analyze imports in payments.py at {git.head()}" in result.err


def test_conventional_src_layout_resolves_packages(
    candidate: tuple[Path, str, str, Record],
) -> None:
    root, _, _, _ = candidate
    git = Git(root)
    git.text("rm", "payments.py", "stripe_adapter.py")
    git.text("commit", "-qm", "Remove root-level packages")
    base = git.head()
    (root / "src").mkdir()
    (root / "src" / "payments.py").write_text("import stripe_adapter\n")
    (root / "src" / "stripe_adapter.py").write_bytes(b"# source with no newline")
    git.text("add", "src")
    git.text("commit", "-qm", "Use conventional src layout")
    assert "Added: gateway → adapter" in _review(root, base, git.head())


def test_no_prefixes_skips_dependency_analysis(candidate: tuple[Path, str, str, Record]) -> None:
    root, base, _, _ = candidate
    project = open_store(root)
    for name in ("gateway", "adapter"):
        component = project.resolve("composer:component", name)
        project.supersede(component["id"], payload={"module_prefixes": []})
    git = Git(root)
    (root / "payments.py").write_text("def broken(\n")
    git.text("add", "payments.py")
    git.text("commit", "-qm", "Add unmapped source")
    brief = _review(root, base, git.head())
    assert "No component module mappings declared." in brief
    assert "Added:" not in brief.split("## Observed component dependency changes", 1)[1]


def test_review_identifies_new_import_of_existing_unmapped_module(
    candidate: tuple[Path, str, str, Record],
) -> None:
    root, _, base, _ = candidate
    git = Git(root)
    (root / "payments.py").write_text("import stripe_adapter\nimport helpers\n")
    git.text("add", "payments.py")
    git.text("commit", "-qm", "Import a local helper and remove an external import")
    brief = _review(root, base, git.head()).split("## Observed component dependency changes", 1)[1]
    assert "Added imports of unmapped first-party modules (gateway imports helpers)" in brief
    assert "unknown_vendor" not in brief
