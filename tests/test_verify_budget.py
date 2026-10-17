"""Verification stays on the phase's checks, and a failing check does not edit."""

from __future__ import annotations

import re

from conftest import REPO_ROOT

SKILLS = REPO_ROOT / "skills"

FORBIDDEN_CHAIN = '-n 4 -m "not tmux"'


def _text(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text()


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
    assert "verification task's acceptances come from the phase exit criteria" in text
    assert "one is an integration check through the real entry point" in text


def test_plan_phase_rejects_whole_suite_and_unfiltered_app_file():
    text = _flat(_text("plan-phase"))
    assert "whole `tests` tree" in text
    assert "`tests/test_dashboard_app.py` without a `-k` filter for this phase" in text
    assert "is not a verification acceptance" in text


def test_close_instructions_use_the_task_command():
    for name in ("AGENTS.md", "CLAUDE.md"):
        section = _testing_section(name)
        assert "`verify_command`" in section
        chain_at = section.find(FORBIDDEN_CHAIN)
        assert chain_at < 0 or "-m tmux" not in section[chain_at:]
        assert "run the full suite" not in section
        assert "full suite" not in section or "clos" not in section


def test_verification_failure_does_not_edit():
    execute = _flat(_text("execute-phase"))
    assert "The verification executor returns `fail` and does not edit the tree." in execute

    verify = _flat(_text("verify-work"))
    assert (
        "leave the work-item `in_progress` and use assessment `next` `execute`"
        in verify
    )
    assert "a suite the acceptance does not name" in verify


def test_per_task_verify_stays_scoped_while_phase_suite_is_documented():
    """Per-task verify_command stays scoped; phase-level suite is the full run."""
    execute = _flat(_text("execute-phase"))
    assert "whole-suite" in execute or "whole suite" in execute or "full suite" in execute
    assert "phase_gate.suite" in execute or "phase-level" in execute
    assert "per-task" in execute and "scoped" in execute
    assert "verify_command" in execute
    assert "tier-2" not in execute and "tier2" not in execute

    reviewer = (REPO_ROOT / "agents" / "se-reviewer.md").read_text()
    assert "tier-2" not in reviewer and "tier2" not in reviewer

    readme = _testing_section("README.md")
    assert "phase_gate.suite" in readme
    assert "phase-level" in readme or "phase level" in readme
    assert "Per-task" in readme or "per-task" in readme
    assert "narrowly scoped" in readme or "scoped" in readme
    for mode in ("none", "smoke", "full", "external"):
        assert mode in readme
    for gate in ("required", "advisory", "deferred"):
        assert gate in readme
    assert "mode=full" in readme and "gate=advisory" in readme
    assert "<phase>-suite" in readme or "`<phase>-suite`" in readme
    assert "tier-2" not in readme and "tier2" not in readme
    # README documents the phase-level suite; AGENTS/CLAUDE close
    # instructions must not tell a task to run it.
    for name in ("AGENTS.md", "CLAUDE.md"):
        section = _testing_section(name)
        assert "`verify_command`" in section
        assert "run the full suite" not in section


def test_plan_phase_still_rejects_whole_suite_on_verification_task():
    text = _flat(_text("plan-phase"))
    assert "whole `tests` tree" in text
    assert "is not a verification acceptance" in text
