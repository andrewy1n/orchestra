from __future__ import annotations

import pytest

from orchestra.conductor.briefs.render import BriefContext, render_brief

PROMPT_MARKER = (
    "You are the orchestra phase-end reviewer. You grade the phase against its\n"
    "stated intent, not against the builder's self-reports."
)
FALLBACK_INSTRUCTION = (
    "Use the `reviewer` subagent when the host provides one. "
    "Otherwise give the prompt below to a general read-only subagent."
)


def _flat(text: str) -> str:
    return " ".join(text.split())


def _brief(step: str, stage: str | None, adapter: str = "github-pr") -> str:
    ctx = BriefContext(
        step=step,
        phase="demo",
        effort="demo-effort",
        stage=stage,
        adapter=adapter,
        weight="full",
    )
    return render_brief(ctx)


@pytest.mark.parametrize("step", ["execute", "verify"])
def test_reviewer_fallback_brief_contains_reviewer_prompt(step: str) -> None:
    assert _flat(PROMPT_MARKER) in _flat(_brief(step, "reviewer"))


@pytest.mark.parametrize("step", ["execute", "verify"])
def test_reviewer_fallback_brief_contains_fallback_instruction(step: str) -> None:
    assert _flat(FALLBACK_INSTRUCTION) in _flat(_brief(step, "reviewer"))


def test_reviewer_fallback_execute_brief_is_non_empty_with_phase_filled() -> None:
    text = _brief("execute", None)

    assert text.strip()
    assert "demo" in text
    assert "{phase}" not in text
