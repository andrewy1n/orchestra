"""Refunds scenario for standing architecture constraints through the real CLI entry points."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from canon_support import make_project
from conductor_support import _commit_all
from conftest import REPO_ROOT

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import Record
from orchestra.conductor.phases.workflow.workflow_review import record_step_review
from orchestra.conductor.verification.standing_constraints import (
    standing_constraint_status,
)

BIN = REPO_ROOT / "bin" / "orchestra"
EFFORT = "refunds-effort"
PHASE = "refunds"
NAME = "stripe-sdk-isolation"
RULE = "Only billing adapters may import the Stripe SDK."
BASIS = "Provider access belongs in billing adapters."
OFFENDING = "refunds.py:3: import stripe"
DESIGN_BODY = (
    "## Architecture\nUse workflow records.\n"
    "## Interfaces\nUse typed APIs.\n"
    "## Decisions\nPersist reviews.\n"
    "## Invariants\nDo not infer approval.\n"
    "## Assumptions\nThe phase exists.\n"
    "## Tradeoffs\nKeep writes atomic.\n"
    "## Risks\nStale inputs need review.\n"
)
PHASE_BODY = (
    "## Problem\nSupport refunds.\n"
    "## Approach\nUse the payments API.\n"
    "## Exit criteria\nVerify the result.\n"
    "## Landing\nUse a phase worktree.\n"
)
SPEC_BODY = (
    "## Requirements\n\nR1: Refunds work.\n"
    "## Acceptance criteria\n\nRefund API passes.\n"
    "## Constraints\n\nNone.\n"
    "## Non-goals\n\nNone.\n"
    "## Invariants\n\nNone.\n"
    "## Assumptions\n\nNone.\n"
)
SCANNER = (
    "import pathlib, sys\n"
    "bad = []\n"
    "for path in sorted(pathlib.Path('orchestra/payments').glob('*.py')):\n"
    "    for number, line in enumerate(path.read_text().splitlines(), 1):\n"
    "        if line.startswith('import stripe'):\n"
    "            bad.append(f'{path.name}:{number}: {line}')\n"
    "print('\\n'.join(bad))\n"
    "sys.exit(1 if bad else 0)\n"
)


def _orchestra(store: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BIN), *args],
        capture_output=True,
        text=True,
        cwd=str(store),
        timeout=120,
    )


def _set_phase_branch(store: Path) -> None:
    subprocess.run(["git", "branch", "-f", f"phase/{PHASE}", "HEAD"], cwd=store, check=True)


def _declare_rule(project: Project) -> Record:
    return project.create(
        record_type="score:standing-constraint",
        subject=NAME,
        payload={"area": "payments", "rule": RULE, "check": "python3 scan_stripe.py"},
        body=f"## Basis\n\n{BASIS}\n",
    )


def _seed_phase(project: Project) -> Record:
    project.create(
        record_type="score:effort", subject=EFFORT, payload={"goal": "Refunds", "kind": "deliver"}
    )
    project.create(
        record_type="score:phase",
        subject=PHASE,
        payload={"title": PHASE, "ordinal": 1, "effort": EFFORT},
        body=PHASE_BODY,
    )
    specification = project.create(
        record_type="score:specification",
        subject=f"{PHASE}-spec",
        payload={"phase": PHASE, "effort": EFFORT, "requirements": ["R1"], "weight": "full"},
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
    return project.create(
        record_type="score:acceptance",
        subject="refund-api",
        payload={
            "phase": PHASE,
            "effort": EFFORT,
            "requirement": "R1",
            "method": "check",
            "verify_command": "true",
        },
    )


def _scenario(root: Path) -> tuple[Project, Record, str]:
    """Declare, brief, pin, then run both checks at one revision; return the revision."""
    store = root
    project = make_project(root)
    constraint = _declare_rule(project)
    acceptance = _seed_phase(project)

    brief = _orchestra(store, "workflow", "brief", PHASE, "design", "--area", "payments")
    assert brief.returncode == 0, brief.stdout + brief.stderr
    assert "Applicable standing constraints" in brief.stdout
    assert RULE in brief.stdout
    assert BASIS in brief.stdout

    project.create(
        record_type="score:design",
        subject=f"{PHASE}-design",
        payload={
            "phase": PHASE,
            "effort": EFFORT,
            "decisions": [],
            "standing_constraints": [constraint["id"]],
        },
        body=DESIGN_BODY,
    )
    payments = store / "orchestra" / "payments"
    payments.mkdir(parents=True)
    (payments / "refunds.py").write_text("from __future__ import annotations\n\nimport stripe\n")
    (store / "scan_stripe.py").write_text(SCANNER)
    (store / ".gitignore").write_text(".canon/canon.db*\n")
    revision = _commit_all(store, "seed refunds")
    _set_phase_branch(store)

    passed = _orchestra(store, "check", "--acceptance", acceptance["id"])
    assert passed.returncode == 0, passed.stdout + passed.stderr
    failed = _orchestra(store, "check", "--standing-constraint", NAME, "--phase", PHASE)
    assert failed.returncode == 1, failed.stdout + failed.stderr
    assert OFFENDING in json.loads(failed.stdout)["record"]["body"]
    return project, constraint, revision


def test_refund_passes_while_stripe_constraint_violation_is_reported(tmp_path: Path) -> None:
    store = tmp_path / "repo"
    _, constraint, _ = _scenario(store)

    view = _orchestra(store, "view", "verification")

    assert view.returncode == 0, view.stdout + view.stderr
    text = view.stdout
    assert "- **R1**: verified" in text
    block = text.split("### Standing constraints\n", 1)[1]
    assert f"- **{NAME}** (payments): violated" in block
    assert constraint["id"] in block
    assert OFFENDING in block
    assert text.index("- **R1**: verified") < text.index("### Standing constraints")


def test_constraint_without_evidence_at_new_revision_is_unverified(tmp_path: Path) -> None:
    store = tmp_path / "repo"
    project, constraint, revision_a = _scenario(store)
    (store / "NOTES.md").write_text("later change\n")
    revision_b = _commit_all(store, "later change")
    _set_phase_branch(store)
    assert revision_b != revision_a

    records = open_store(store).records()
    at_a = standing_constraint_status(records, PHASE, revision_a)
    at_b = standing_constraint_status(records, PHASE, revision_b)

    assert [(o.name, o.outcome) for o in at_a] == [(NAME, "violated")]
    assert OFFENDING in at_a[0].evidence
    assert [(o.name, o.outcome, o.check_run_id) for o in at_b] == [(NAME, "unverified", None)]

    view = _orchestra(store, "view", "verification")

    assert view.returncode == 0, view.stdout + view.stderr
    block = view.stdout.split("### Standing constraints\n", 1)[1]
    assert f"- **{NAME}** (payments): unverified" in block
    assert "violated" not in block
    assert revision_b[:7] in block

    revised = project.supersede(
        constraint["id"],
        payload={"area": "payments", "rule": f"{RULE} Tests are exempt.", "check": "true"},
    )["record"]
    after = standing_constraint_status(open_store(store).records(), PHASE, revision_a)

    assert [(o.pinned_id, o.newer_id, o.outcome) for o in after] == [
        (constraint["id"], revised["id"], "violated")
    ]


def test_readopted_constraint_version_is_unverified_until_checked_at_revision(
    tmp_path: Path,
) -> None:
    store = tmp_path / "repo"
    project, constraint, _ = _scenario(store)
    revised = project.supersede(
        constraint["id"],
        payload={
            "area": "payments",
            "rule": f"{RULE} Tests are exempt.",
            "check": "python3 scan_stripe.py",
        },
    )["record"]
    design = next(r for r in open_store(store).records() if r["record_type"] == "score:design")
    project.supersede(
        design["id"],
        payload={**design["payload"], "standing_constraints": [revised["id"]]},
    )

    before = _orchestra(store, "view", "verification")

    assert before.returncode == 0, before.stdout + before.stderr
    block = before.stdout.split("### Standing constraints\n", 1)[1]
    assert f"- **{NAME}** (payments): unverified" in block
    assert revised["id"] in block

    checked = _orchestra(store, "check", "--standing-constraint", NAME, "--phase", PHASE)
    assert checked.returncode == 1, checked.stdout + checked.stderr

    after = _orchestra(store, "view", "verification")

    block = after.stdout.split("### Standing constraints\n", 1)[1]
    assert f"- **{NAME}** (payments): violated" in block
    assert revised["id"] in block
