"""Guard the phase verification-gate rules in the skills against drift."""

from __future__ import annotations

import re

import pytest
from conftest import REPO_ROOT
from helpers import skill_text
from skill_extraction import extract_invocations

SKILLS_ROOT = REPO_ROOT / "skills"


def _skill(name: str) -> str:
    return skill_text(name)


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


@pytest.mark.parametrize(
    "phrase",
    [
        "## Verification task For a `deliver` or `repair` phase, create last",
        "with every other work-item subject in `depends_on`",
        "One thin acceptance per exit criterion",
        "integration check through the real entry point",
    ],
)
def test_plan_phase_requires_a_verification_task(phrase):
    assert phrase in _normalized(_skill("plan-phase"))


def test_plan_phase_example_verification_task_depends_on_several_work_items():
    creates = [
        inv
        for inv in extract_invocations(_skill("plan-phase"))
        if inv["subcommand"] == "create"
        and inv["type"] == "score:work-item"
        and "verify-<phase-slug>" in inv["raw"]
    ]
    assert len(creates) == 1
    assert len(creates[0]["payload"]["depends_on"]) >= 2


def test_plan_phase_example_gives_the_verification_task_an_integration_acceptance():
    acceptances = [
        inv
        for inv in extract_invocations(_skill("plan-phase"))
        if inv["subcommand"] == "create"
        and inv["type"] == "score:acceptance"
        and "verify-<phase-slug>" in inv["raw"]
    ]
    assert any(
        "integration" in (inv["payload"] or {}).get("verify_command", "") for inv in acceptances
    )


@pytest.mark.parametrize(
    "phrase",
    [
        "Each exit criterion states how it is verified",
        "propose a final end-to-end verification phase",
    ],
)
def test_init_requires_verifiable_exit_criteria(phrase):
    assert phrase in _normalized(_skill("init"))


@pytest.mark.parametrize(
    "phrase",
    [
        "check the gate below before closing",
        "Verification task exists and is `done`",
        "latest check-run per `criterion_id` passes",
        "Gate fails → leave phase `in_progress`",
        "Close a phase whose phase-end gate does not hold",
    ],
)
def test_execute_phase_gates_phase_close(phrase):
    assert phrase in _normalized(_skill("execute-phase"))


def test_execute_phase_queries_check_runs_by_criterion_before_closing():
    text = _skill("execute-phase")
    gate_query = text.index("--where payload.criterion_id=<acceptance-id>")
    phase_close = text.index(
        "canon update --type score:phase --id <phase-id> \\\n  --transition done"
    )
    assert gate_query < phase_close
