from __future__ import annotations

from pathlib import Path

import pytest
from conductor_support import Cli, seed

from orchestra.canon.project import open_store
from orchestra.conductor.briefs.render import BriefContext, render_brief

APPROVAL_SENTENCE = "Wait for explicit user approval or delegation before you record it"
PLAN_REVIEW_SKIP = "Skip this gate at `auto-plan` and `auto-phases`"
PLAN_STEPS = ("spec", "design", "tasks")


def _flat(text: str) -> str:
    return " ".join(text.split())


def _brief(step: str) -> str:
    ctx = BriefContext(
        step=step,
        phase="demo",
        effort="demo-effort",
        stage=None,
        adapter="github-pr",
        weight="full",
    )
    return _flat(render_brief(ctx))


@pytest.mark.parametrize("step", ["spec", "design"])
def test_approval_gate_brief_states_user_approval_sentence(step: str) -> None:
    assert APPROVAL_SENTENCE in _brief(step)


@pytest.mark.parametrize("step", PLAN_STEPS)
def test_approval_gate_brief_states_review_command_with_phase_filled(step: str) -> None:
    text = _brief(step)

    assert f"orchestra workflow review demo {step}" in text
    assert "{phase}" not in text


def test_approval_gate_tasks_brief_states_plan_review_gate() -> None:
    assert PLAN_REVIEW_SKIP in _brief("tasks")


def test_approval_gate_render_writes_no_record(store: Path, cli: Cli) -> None:
    seed(store, cli)
    project = open_store(store)
    token = project.change_token()
    records = project.records()

    for step in PLAN_STEPS:
        _brief(step)

    after = open_store(store)
    assert after.change_token() == token
    assert after.records() == records
