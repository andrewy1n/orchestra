"""orchestra check --standing-constraint runs a pinned constraint and records a check-run."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conductor_support import _commit_all, record_fixture_design_review
from conftest import REPO_ROOT

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import Record
from orchestra.conductor.verification.standing_constraints import (
    criterion_id,
    standing_constraint_status,
)

BIN = REPO_ROOT / "bin" / "orchestra"
EFFORT = "refunds-effort"
PHASE = "refunds"
NAME = "stripe-sdk-isolation"
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


def _seed(
    store: Path, *, offending: bool, pin: bool = True, approved: bool = True
) -> tuple[Project, Record]:
    payments = store / "orchestra" / "payments"
    payments.mkdir(parents=True)
    imports = "import stripe" if offending else "import json"
    (payments / "refunds.py").write_text(f"from __future__ import annotations\n\n{imports}\n")
    (store / "scan_stripe.py").write_text(SCANNER)
    project = open_store(store)
    project.create(
        record_type="score:effort", subject=EFFORT, payload={"goal": "Refunds", "kind": "deliver"}
    )
    project.create(
        record_type="score:phase",
        subject=PHASE,
        payload={"title": PHASE, "ordinal": 1, "effort": EFFORT},
        body="## Problem\nRefunds.\n## Approach\nAPI.\n## Exit criteria\nDone.\n",
    )
    constraint = project.create(
        record_type="score:standing-constraint",
        subject=NAME,
        payload={
            "area": "payments",
            "rule": "Only billing adapters may import the Stripe SDK.",
            "check": "python3 scan_stripe.py",
        },
        body="## Basis\n\nProvider access belongs in billing adapters.\n",
    )
    design = project.create(
        record_type="score:design",
        subject="refunds-design",
        payload={
            "phase": PHASE,
            "effort": EFFORT,
            "decisions": [],
            "standing_constraints": [constraint["id"]] if pin else [],
        },
        body=DESIGN_BODY,
    )
    if approved:
        record_fixture_design_review(project, design)
    _commit_all(store, "seed refunds")
    return project, constraint


def _check(store: Path, name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BIN), "check", "--standing-constraint", name, "--phase", PHASE],
        capture_output=True,
        text=True,
        cwd=str(store),
        timeout=60,
    )


def _head(store: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(store), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()


def test_failing_constraint_check_records_offending_file_and_line(store: Path) -> None:
    project, constraint = _seed(store, offending=True)

    result = _check(store, NAME)

    assert result.returncode == 1, result.stdout + result.stderr
    record = json.loads(result.stdout)["record"]
    assert record["record_type"] == "tuner:check-run"
    assert record["payload"]["criterion_id"] == criterion_id(constraint["id"])
    assert record["payload"]["revision"] == _head(store)
    assert record["payload"]["result"] == "fail"
    assert record["payload"]["runner"] == "orchestra"
    assert OFFENDING in record["body"]
    outcomes = standing_constraint_status(project.records(), PHASE, _head(store))
    assert [(o.name, o.outcome, o.check_run_id) for o in outcomes] == [
        (NAME, "violated", record["id"])
    ]
    assert OFFENDING in outcomes[0].evidence


def test_passing_constraint_check_verifies_constraint(store: Path) -> None:
    project, constraint = _seed(store, offending=False)

    result = _check(store, NAME)

    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(result.stdout)["record"]
    assert record["payload"]["criterion_id"] == criterion_id(constraint["id"])
    assert record["payload"]["result"] == "pass"
    outcomes = standing_constraint_status(project.records(), PHASE, _head(store))
    assert [(o.outcome, o.check_run_id) for o in outcomes] == [("verified", record["id"])]


def test_unpinned_constraint_name_is_refused_without_check_run(store: Path) -> None:
    project, _ = _seed(store, offending=True, pin=False)
    before = [r for r in project.records() if r["record_type"] == "tuner:check-run"]

    result = _check(store, NAME)

    assert result.returncode != 0
    assert NAME in result.stderr + result.stdout
    assert "pinned" in (result.stderr + result.stdout).lower()
    after = [r for r in open_store(store).records() if r["record_type"] == "tuner:check-run"]
    assert len(after) == len(before)


def test_draft_design_does_not_pin_a_constraint(store: Path) -> None:
    project, _ = _seed(store, offending=False, approved=False)

    result = _check(store, NAME)

    assert result.returncode == 4, result.stdout + result.stderr
    assert "not pinned" in result.stderr
    assert standing_constraint_status(project.records(), PHASE, _head(store)) == []
