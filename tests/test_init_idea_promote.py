"""Contract tests for init promoting a composer:idea from engage routing."""

from __future__ import annotations

from conftest import REPO_ROOT
from helpers import skill_text
from skill_extraction import extract_invocations

SKILLS = REPO_ROOT / "skills"


def _text(name: str) -> str:
    return skill_text(name)


def test_init_documents_idea_routing_and_skip():
    text = _text("init")
    lower = text.lower()
    assert "idea: <subject>" in text or "idea:" in lower
    assert "idea: none" in lower or "`none`" in text
    assert "engage" in lower


def test_init_promotes_idea_after_effort_and_position():
    invs = extract_invocations((SKILLS / "init" / "SKILL.md").read_text())
    idea_lists = [
        inv for inv in invs if inv["subcommand"] == "list" and inv["type"] == "composer:idea"
    ]
    assert len(idea_lists) == 1
    raw = idea_lists[0]["raw"]
    assert "--exact-subject" in raw
    assert "--full" in raw
    promotes = [
        inv
        for inv in invs
        if inv["subcommand"] == "supersede"
        and inv["type"] == "composer:idea"
        and (inv.get("payload") or {}).get("status") == "promoted"
    ]
    assert len(promotes) == 1
    payload = promotes[0]["payload"]
    assert payload["effort"] == "<effort-slug>"
    assert "phase" not in payload
