from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject
from orchestra.canon.validation import ValidationError
from orchestra.score.analyze import analyze_phase

FREEZE: JsonObject = {
    "test_ids": ["tests/test_probe.py::test_probe"],
    "oracle_hashes": ["tests/test_probe.py:sha256:" + "a" * 64],
}


def _phase(project: Project, **payload: str) -> None:
    create(
        project,
        "score:phase",
        "policy",
        {"title": "Policy", "ordinal": 2, "effort": "alpha", "weight": "light", **payload},
        "## Problem\n\nPolicy.\n\n## Approach\n\nCheck.\n\n## Exit criteria\n\nPass.\n\n## Requirements\n\nR1: Behavior.\n",
    )
    create(
        project,
        "score:work-item",
        "probe",
        {
            "title": "Probe",
            "phase": "policy",
            "effort": "alpha",
            "kind": "repair",
            "assignee": "",
            "requirements": ["R1"],
        },
    )


def _acceptance(project: Project, payload: JsonObject) -> None:
    create(
        project,
        "score:acceptance",
        "probe",
        {
            "method": "tdd",
            "phase": "policy",
            "effort": "alpha",
            "verify_command": "true",
            "requirement": "R1",
            **payload,
        },
    )


def test_analyze_rejects_partial_legacy_freeze(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    seed_effort(project)
    _phase(project)
    _acceptance(project, {"test_ids": FREEZE["test_ids"]})
    report = analyze_phase(project.records(), "policy")
    assert not report.ok
    assert "oracle-policy-invalid" in {finding.code for finding in report.findings}


@pytest.mark.parametrize("policy", ["none", "frozen"])
def test_schema_accepts_phase_oracle_policy(tmp_path: Path, policy: str) -> None:
    project = make_project(tmp_path)
    seed_effort(project)
    _phase(project, oracle_policy=policy)
    assert project.validate() == []


def test_schema_rejects_unknown_policy(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    seed_effort(project)
    with pytest.raises(ValidationError, match="oracle_policy"):
        _phase(project, oracle_policy="optional")


@pytest.mark.parametrize(
    ("phase_policy", "payload", "valid"),
    [
        ("none", {}, True),
        ("none", {"oracle_policy": "none"}, True),
        ("none", FREEZE, True),
        ("frozen", FREEZE, True),
        ("frozen", {"oracle_policy": "none"}, True),
        ("none", {"oracle_policy": "frozen", **FREEZE}, True),
        ("none", {"oracle_policy": "none", **FREEZE}, False),
        ("none", {"oracle_policy": "frozen"}, False),
        ("frozen", {}, False),
        ("none", {"oracle_hashes": FREEZE["oracle_hashes"]}, False),
        ("none", {"oracle_policy": "frozen", **FREEZE, "method": "manual"}, False),
        ("none", {**FREEZE, "method": "check"}, True),
        ("none", {**FREEZE, "test_ids": ["unfrozen.py::test_probe"]}, False),
    ],
)
def test_analyze_policy_matrix(
    tmp_path: Path, phase_policy: str, payload: JsonObject, valid: bool
) -> None:
    project = make_project(tmp_path)
    seed_effort(project)
    _phase(project, oracle_policy=phase_policy)
    _acceptance(project, payload)
    report = analyze_phase(project.records(), "policy")
    assert report.ok is valid, report.findings


def test_missing_policy_keeps_ordinary_tdd_valid(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    seed_effort(project)
    _phase(project)
    _acceptance(project, {})
    assert analyze_phase(project.records(), "policy").ok
