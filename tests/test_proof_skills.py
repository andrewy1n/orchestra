"""Skills require ## Proof and assemble project:proof-packet at phase end."""

from __future__ import annotations

from conftest import REPO_ROOT

SKILLS = REPO_ROOT / "skills"


def _text(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text()


def test_settle_and_plan_require_proof_section():
    settle = _text("settle-phase")
    plan = _text("plan-phase")
    assert "## Proof" in settle
    assert "demo" in settle and "claims" in settle and "audit-triage" in settle
    assert "## Proof" in plan
    assert "kind" in plan
    assert "look intent" in plan
    assert "Proof checks for incidental" in plan or "Proof checks" in plan


def test_execute_assembles_proof_packet():
    text = _text("execute-phase")
    assert "project:proof-packet" in text
    assert "## Look" in text and "## Machine" in text
    assert "## Attention" in text and "## Diff" in text
    assert "Refuse to say the phase is complete without" in text or "Refuse to say the phase is complete" in text
    assert "proof-packet" in text
    assert "payload.revision" in text
    assert "Call the phase complete" in text or "without a `project:proof-packet`" in text


def test_execute_aff_hooks_and_incidental():
    text = _text("execute-phase")
    assert ".affidavit/manifest.json" in text
    assert "aff trail" in text
    assert "aff audit" in text
    assert "Incidental" in text or "incidental" in text
    assert "no-Landing" in text or "no Landing" in text or "Landing is absent" in text
