from __future__ import annotations

from conftest import REPO_ROOT


def test_engage_skill_names_orchestra_place():
    text = (REPO_ROOT / "skills" / "engage" / "SKILL.md").read_text()
    assert "orchestra place" in text
