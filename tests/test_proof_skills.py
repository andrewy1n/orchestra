"""Skills require ## Proof and assemble conductor:proof-packet at phase end."""

from __future__ import annotations

from conftest import REPO_ROOT
from helpers import skill_text

SKILLS = REPO_ROOT / "skills"


def _text(name: str) -> str:
    return skill_text(name)


def test_settle_and_plan_require_proof_section():
    settle = _text("settle-phase")
    plan = _text("plan-phase")
    assert "## Proof" in settle
    assert "demo" in settle and "claims" in settle and "audit-triage" in settle
    assert "## Proof" in plan
    assert "`## Proof`: `kind` (`demo`|`commands`|`claims`|`audit-triage`|`mixed`) + one sentence on look intent" in " ".join(plan.split())


def test_execute_assembles_proof_packet():
    text = _text("execute-phase")
    assert "conductor:proof-packet" in text
    assert "## Look" in text and "## Machine" in text
    assert "## Attention" in text and "## Diff" in text
    assert 'Refuse "phase complete" without a packet' in text
    assert "proof-packet" in text
    assert "`revision` = phase-head" in " ".join(text.split())
    assert "Call the phase complete" in text or "without a `conductor:proof-packet`" in text


def test_execute_tuner_hooks_and_incidental():
    text = _text("execute-phase")
    assert ".tuner/manifest.json" in text
    assert "orchestra verify trail" in text
    assert "orchestra verify audit" in text
    assert "Incidental" in text or "incidental" in text
    assert "no-Landing" in text or "no Landing" in text or "Landing is absent" in text
