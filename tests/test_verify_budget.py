"""Verification stays on the phase's checks, and a failing check does not edit."""

from __future__ import annotations

import re

from conftest import REPO_ROOT
from helpers import skill_text

SKILLS = REPO_ROOT / "skills"


def _text(name: str) -> str:
    return skill_text(name)


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _testing_section(name: str) -> str:
    text = (REPO_ROOT / name).read_text()
    start = text.index("## Testing")
    rest = text[start + len("## Testing") :]
    end = rest.find("\n## ")
    section = rest if end < 0 else rest[:end]
    return _flat(section)


def test_plan_phase_limits_verification_to_phase_checks():
    text = _flat(_text("plan-phase"))
    assert "Acceptances come from phase exit criteria; at least one is an integration check through the real entry point." in text


def test_plan_phase_rejects_whole_suite_and_unfiltered_app_file():
    text = _flat(_text("plan-phase"))
    assert "whole `tests` tree" in text
    assert "`tests/test_dashboard_app.py` without a `-k` filter for this phase" in text
    assert "is not a verification acceptance" in text


def test_verification_failure_does_not_edit():
    execute = _flat(_text("execute-phase"))
    assert "run phase checks; return `fail`; do not edit the tree" in execute
    assert "Let the verification executor edit the tree" in execute

    verify = _flat(_text("verify-work"))
    assert "When a verification check fails for that reason, same routing" in verify
    assert "a suite the acceptance does not name" in verify


def test_per_task_verify_stays_scoped_while_phase_suite_is_documented():
    """Per-task verify_command stays scoped; phase-level suite is the full run."""
    execute = _flat(_text("execute-phase"))
    assert "Put a whole-suite command on a per-task `verify_command`" in execute
    assert "phase_gate.suite" in execute
    assert "tier-2" not in execute and "tier2" not in execute

    reviewer = (REPO_ROOT / "agents" / "se-reviewer.md").read_text()
    assert "tier-2" not in reviewer and "tier2" not in reviewer

    readme = _testing_section("README.md")
    assert "phase_gate.suite" in readme
    assert "phase-level suite" in readme
    assert "Per-task `verify_command` values stay narrowly scoped" in readme
    for mode in ("none", "smoke", "full", "external"):
        assert mode in readme
    for gate in ("required", "advisory", "deferred"):
        assert gate in readme
    assert "`mode=full` and `gate=required`" in readme
    assert "`<phase>-suite`" in readme
    assert "tier-2" not in readme and "tier2" not in readme


def test_plan_phase_still_rejects_whole_suite_on_verification_task():
    text = _flat(_text("plan-phase"))
    assert "whole `tests` tree" in text
    assert "is not a verification acceptance" in text
