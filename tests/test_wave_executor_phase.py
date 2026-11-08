"""tasks and execute agree on inline and subagent waves."""

from __future__ import annotations

import re

from conftest import REPO_ROOT
from helpers import skill_text

SKILLS = REPO_ROOT / "skills"


def _text(name: str) -> str:
    raw = skill_text(name)
    return re.sub(r"\s+", " ", raw)


def test_both_skills_name_the_same_executors():
    plan = _text("tasks")
    execute = _text("execute")
    for text in (plan, execute):
        assert "`inline`" in text
        assert "`subagent`" in text


def test_both_skills_treat_a_missing_executor_as_subagent():
    assert "Missing means `subagent`" in _text("tasks")
    assert "missing/empty → `subagent`" in _text("execute")


def test_execute_stops_when_a_wave_disagrees():
    text = _text("execute")
    assert (
        "If the wave disagrees, or any value is other than those two, stop and name the tasks"
        in text
    )
    assert "Spawn a subagent for `inline`, or spawn when the wave disagrees on executor" in text
