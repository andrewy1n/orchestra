"""R4: aff audit reports the red-first revision-on-tdd relaxation as unclaimed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
AFF = REPO / "bin" / "aff"
PROBES = REPO / "tests" / "fixtures" / "red_first_tdd_revision_probes.json"
RANGE_BASE = "b3159b6"
RANGE_TIP = "c14dedb"


def _require_history() -> None:
    for sha in (RANGE_BASE, RANGE_TIP):
        probe = subprocess.run(
            ["git", "-C", str(REPO), "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True,
        )
        if probe.returncode != 0:
            pytest.skip(f"{sha} missing from repository history")


def test_r4_audit_reports_unclaimed_tdd_revision_relaxation():
    """R4: on the red-first range, audit reports revision-on-tdd relaxation as unclaimed."""
    _require_history()
    proc = subprocess.run(
        [
            sys.executable,
            str(AFF),
            "audit",
            "--cwd",
            str(REPO),
            "--base",
            RANGE_BASE,
            "--head",
            RANGE_TIP,
            "--probes",
            str(PROBES),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    payload = json.loads(proc.stdout)
    assert "diffs" in payload
    diffs = [d for d in payload["diffs"] if d.get("probe") == "tdd-revision-relax"]
    assert len(diffs) == 1
    assert "runner_invented_fields" in diffs[0]["base"]["stdout"]
    assert diffs[0]["head"]["stdout"].strip() == "ok"
