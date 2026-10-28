"""Contract tests for the triage-ideas skill (composer idea-triage phase)."""

from __future__ import annotations

from conftest import REPO_ROOT
from helpers import skill_text
from skill_extraction import extract_invocations

SKILLS = REPO_ROOT / "skills"
WRITES = {"create", "update", "supersede", "capture", "apply", "correct", "contradict"}


def _text(name: str) -> str:
    return skill_text(name)


def test_triage_ideas_skill_is_discoverable():
    text = _text("triage-ideas")
    assert text.startswith("---\nname: triage-ideas\n")
    assert "description:" in text.split("---")[1]


def test_triage_ideas_lists_open_ideas_without_area():
    text = _text("triage-ideas")
    lower = text.lower()
    assert "no `area`" in lower or "no area" in lower
    invs = extract_invocations((SKILLS / "triage-ideas" / "SKILL.md").read_text())
    idea_lists = [
        inv for inv in invs
        if inv["subcommand"] == "list" and inv["type"] == "composer:idea"
    ]
    assert len(idea_lists) == 1
    assert "payload.status=open" in idea_lists[0]["raw"]
    assert "--full" in idea_lists[0]["raw"]


def test_triage_ideas_lists_areas():
    invs = extract_invocations((SKILLS / "triage-ideas" / "SKILL.md").read_text())
    area_lists = [
        inv for inv in invs
        if inv["subcommand"] == "list" and inv["type"] == "composer:area"
    ]
    assert len(area_lists) == 1
    assert "--full" in area_lists[0]["raw"]


def test_triage_ideas_writes_area_and_idea_supersedes():
    invs = extract_invocations((SKILLS / "triage-ideas" / "SKILL.md").read_text())
    written = {
        inv["type"]
        for inv in invs
        if inv["subcommand"] in WRITES
    }
    assert written == {"composer:area", "composer:idea"}
    creates = [
        inv for inv in invs
        if inv["subcommand"] == "create" and inv["type"] == "composer:area"
    ]
    assert len(creates) == 1
    assert creates[0]["payload"]["title"]
    text = (SKILLS / "triage-ideas" / "SKILL.md").read_text()
    assert "## Scope" in text


def test_triage_ideas_assigns_area_via_supersede():
    invs = extract_invocations((SKILLS / "triage-ideas" / "SKILL.md").read_text())
    area_supersedes = [
        inv for inv in invs
        if inv["subcommand"] == "supersede"
        and inv["type"] == "composer:idea"
        and inv.get("payload", {}).get("area")
    ]
    assert len(area_supersedes) == 2
    assert all(inv["payload"]["area"] == "<area-slug>" for inv in area_supersedes)


def test_triage_ideas_dismisses_via_supersede():
    invs = extract_invocations((SKILLS / "triage-ideas" / "SKILL.md").read_text())
    dismiss = [
        inv for inv in invs
        if inv["subcommand"] == "supersede"
        and inv["type"] == "composer:idea"
        and inv.get("payload", {}).get("status") == "dismissed"
    ]
    assert len(dismiss) == 1


def test_triage_ideas_names_engage_and_never_promotes():
    text = _text("triage-ideas")
    assert "`engage`" in text
    invs = extract_invocations((SKILLS / "triage-ideas" / "SKILL.md").read_text())
    idea_supersedes = [
        inv for inv in invs
        if inv["subcommand"] == "supersede" and inv["type"] == "composer:idea"
    ]
    for inv in idea_supersedes:
        payload = inv.get("payload") or {}
        assert payload.get("status") != "promoted"
    lower = text.lower()
    assert "never sets status" in lower or "never set" in lower
    assert "promoted" in lower


def test_triage_ideas_parent_session_writes():
    lower = _text("triage-ideas").lower()
    assert "parent session writes" in lower
    assert "subagents" in lower
