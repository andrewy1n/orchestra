"""Orchestra skills run orchestra check and orchestra close-batch.

A skill that records a ``tdd`` or ``check`` result runs ``orchestra check``.
A skill that closes a work-item runs ``orchestra close-batch``.
A skill that judges a claim in the manifest runs ``orchestra verify verdict`` and
treats a non-zero exit as not done.
"""

from __future__ import annotations

import re
from pathlib import Path

from conftest import REPO_ROOT
from helpers import skill_text

SKILLS = REPO_ROOT / "skills"
EXECUTE = SKILLS / "execute-phase" / "SKILL.md"
VERIFY = SKILLS / "verify-work" / "SKILL.md"
PLAN = SKILLS / "plan-phase" / "SKILL.md"

# Command tokens, including a line break between the words and `bin/aff check`.
# `aff check-run` names the record, not the command. `aff verdict` stays.
_AFF_CHECK = re.compile(r"(?<![\w.-])aff\s+check\b(?!-)")
_AFF_CLOSE = re.compile(r"(?<![\w.-])aff\s+close-batch\b")

_NOT_DONE = "A non-zero exit means the acceptance is not done."


def command_violations(text: str) -> list[str]:
    """aff commands a skill still tells the agent to run."""
    found: list[str] = []
    if _AFF_CHECK.search(text):
        found.append("aff check")
    if _AFF_CLOSE.search(text):
        found.append("aff close-batch")
    return found


def scan_skills(skills_root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(skills_root.rglob("*.md")):
        for item in command_violations(path.read_text()):
            violations.append(f"{path.relative_to(skills_root)}: tells the agent to run {item}")
    return violations


def test_fixture_old_aff_commands_fail_and_record_names_do_not():
    bad = "Run `aff check --acceptance <id>` then `aff close-batch`.\n"
    assert command_violations(bad) == ["aff check", "aff close-batch"]
    wrapped = "if needed so `aff\n      check` can run.\nbin/aff close-batch\n"
    assert command_violations(wrapped) == ["aff check", "aff close-batch"]
    ok = (
        "Captures aff check-run evidence.\n"
        "Run `orchestra check` and `orchestra close-batch`.\n"
        "orchestra check --acceptance <id>\n"
        "aff verdict --cwd <repo-or-worktree> --at <revision> <claim-id>\n"
        "`aff` is the verdict command on PATH.\n"
    )
    assert command_violations(ok) == []


def test_skills_run_orchestra_check_and_close_batch():
    violations = scan_skills(SKILLS)
    assert not violations, "\n".join(violations)
    for path in (EXECUTE, VERIFY, PLAN):
        text = path.read_text()
        assert "orchestra check" in text, path
    verify = skill_text("verify-work")
    assert "orchestra close-batch" in verify
    assert "orchestra verify verdict" in verify


def test_execute_phase_and_verify_work_run_verify_verdict_for_a_manifest_claim():
    for path, not_done in (
        (EXECUTE, _NOT_DONE),
        (VERIFY, "run `orchestra verify verdict`; non-zero → not done."),
    ):
        text = path.read_text()
        assert "orchestra verify verdict" in text, path
        assert ".tuner/manifest.json" in text, path
        assert not_done in " ".join(text.split()), path
        assert re.search(r"orchestra verify verdict\b[^\n]*<claim-id>", text), path
