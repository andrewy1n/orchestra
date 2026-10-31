"""execute-phase runs a wave inline in this session or as one subagent per task."""

from __future__ import annotations

import re

from conftest import REPO_ROOT
from helpers import skill_text

SKILLS = REPO_ROOT / "skills"


def _text(name: str) -> str:
    raw = skill_text(name)
    return re.sub(r"\s+", " ", raw)


def test_missing_executor_means_subagent_and_disagreement_stops():
    text = _text("execute-phase")
    assert (
        "Read `payload.executor` on each ready task (`inline` | `subagent`; missing/empty → `subagent`)"
        in text
    )
    assert (
        "If the wave disagrees, or any value is other than those two, stop and name the tasks — do not spawn or transition."
        in text
    )


def test_subagent_wave_is_one_worker_per_task():
    text = _text("execute-phase")
    assert "one `generalPurpose` subagent per task, parallel within the wave" in text


def test_inline_wave_runs_in_this_session_and_still_verifies():
    text = _text("execute-phase")
    assert (
        "**`inline`:** this session implements with the same brief, orientation, and kind "
        "instructions; still writes the execution-report and runs `verify-work`"
    ) in text
    assert "**Single-writer:** only this parent may write via `canon`." in text


def test_approach_is_followed_without_asking_for_a_recipe():
    text = _text("execute-phase")
    assert (
        "Follow `## Approach` in the brief; do not ask the user for an implementation recipe when it is present."
    ) in text
