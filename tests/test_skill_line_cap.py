from __future__ import annotations

import pytest
from conftest import REPO_ROOT

LINE_CAP = 150
CAPPED_SKILLS = ("execute-phase", "plan-phase", "verify-work")
EXECUTE = REPO_ROOT / "skills" / "execute-phase" / "SKILL.md"


def line_count(text: str) -> int:
    return len(text.splitlines())


def exceeds_cap(text: str) -> bool:
    return line_count(text) > LINE_CAP


@pytest.mark.parametrize("name", CAPPED_SKILLS)
def test_r15_skill_is_at_most_150_lines(name: str) -> None:
    text = (REPO_ROOT / "skills" / name / "SKILL.md").read_text()
    assert not exceeds_cap(text), f"{name}/SKILL.md has {line_count(text)} lines"


def test_r16_line_cap_flags_an_over_long_skill() -> None:
    assert exceeds_cap("line\n" * 151)
    assert not exceeds_cap("line\n" * 150)


def test_r17_execute_phase_calls_the_three_verbs() -> None:
    text = EXECUTE.read_text()
    for verb in ("orchestra wave start", "orchestra task land", "orchestra wave end"):
        assert verb in text
    assert "git branch task/" not in text and "git merge task/" not in text
    assert "git worktree add" not in text
