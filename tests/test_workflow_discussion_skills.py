"""Check the workflow discussion skills' boundaries and shared Q&A guide."""

from __future__ import annotations

import helpers as h
from conftest import REPO_ROOT
from helpers import skill_text
from skill_extraction import check_skill_text, extract_invocations

SKILLS = REPO_ROOT / "skills"
DEFS = h.schema_defs()


def _text(name: str) -> str:
    return skill_text(name)


def test_spec_writes_only_the_behavioral_contract() -> None:
    text = (SKILLS / "spec" / "SKILL.md").read_text()
    written = {
        inv["type"]
        for inv in extract_invocations(text)
        if inv["subcommand"] in {"create", "supersede", "update", "apply"}
    }

    assert written == {"score:specification"}
    assert "observable behavior" in text
    assert "Do not write technical design" in text
    assert "Do not write" in text and "work-items" in text


def test_design_compares_only_viable_contract_satisfying_options() -> None:
    text = (SKILLS / "design" / "SKILL.md").read_text()
    written = {
        inv["type"]
        for inv in extract_invocations(text)
        if inv["subcommand"] in {"create", "supersede", "update", "apply"}
    }

    assert written == {"score:decision", "score:design"}
    assert "active approved specification" in text
    assert "only approaches that satisfy the specification" in text
    assert "Do not write work-items" in text


def test_context_read_precedes_clarification() -> None:
    for name in ("spec", "design"):
        text = _text(name)
        assert "intent-qa.md" in text
        assert text.index("1. Resolve") < text.index("Apply the shared intent Q&A")
        assert "explicit user approval or delegation" in text


def test_canon_invocations_match_the_schema_modules() -> None:
    for name in ("spec", "design"):
        violations = check_skill_text((SKILLS / name / "SKILL.md").read_text(), DEFS)
        assert not violations, "\n".join(violations)


def test_scenario_guide_covers_the_human_review_requirements() -> None:
    text = (REPO_ROOT / "docs" / "guides" / "workflow-qa-scenarios.md").read_text()
    for requirement in range(30, 43):
        assert f"R{requirement}" in text
    assert "Text checks confirm instruction boundaries" in text


def test_shared_reference_is_packaged_for_both_skills() -> None:
    for name in ("spec", "design"):
        assert (SKILLS / name / "references" / "intent-qa.md").is_file()


def test_direct_steps_end_before_planning() -> None:
    spec = _text("spec")
    design = _text("design")
    assert "A direct spec request ends" in spec
    assert "A direct design request ends" in design
    assert "--stage spec" in spec
    assert "--stage design" in design
    assert "Planning remains a separate workflow step" in design
