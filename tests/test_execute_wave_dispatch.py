"""execute runs a wave inline in this session or as one subagent per task."""

from __future__ import annotations

import re

from conftest import REPO_ROOT


def _text(name: str) -> str:
    raw = (REPO_ROOT / "orchestra" / "conductor" / "briefs" / "sections" / f"{name}.md").read_text()
    return re.sub(r"\s+", " ", raw)


def test_derived_executor_and_conflicting_overrides_stop():
    text = _text("execute-dispatch")
    assert "A written `payload.executor` is an optional `inline` or `subagent` override." in text
    assert "Use the resolved mode for every task in the wave." in text
    assert "Stop before dispatch when any override is invalid or the overrides disagree." in text


def test_subagent_wave_is_one_worker_per_task():
    text = _text("execute-dispatch")
    assert "one `generalPurpose` subagent per task, parallel within the wave" in text


def test_inline_wave_runs_in_this_session_and_still_verifies():
    text = f"{_text('execute-dispatch')} {_text('execute-overview')}"
    assert (
        "**`inline`:** this session implements with the same brief, orientation, and kind "
        "instructions; still writes the execution-report and runs `verify`"
    ) in text
    assert "**Single-writer:** only this parent may write via `canon`." in text


def test_approach_is_followed_without_asking_for_a_recipe():
    text = _text("execute-landing")
    assert (
        "Follow `## Approach` in the brief; do not ask the user for an implementation recipe when it is present."
    ) in text
