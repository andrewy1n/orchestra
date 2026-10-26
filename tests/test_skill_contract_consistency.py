"""Assert every `canon` invocation documented in skills/ names record types,
transitions, and payload keys that the schema modules permit.

Guards against a skill instructing an operation the schemas reject.
"""

from __future__ import annotations

import pytest

import helpers as h
from conftest import REPO_ROOT
from skill_extraction import check_invocation, check_skill_text, extract_invocations, skill_markdown_files

SKILLS_ROOT = REPO_ROOT / "skills"
DEFS = h.schema_defs()


def _skill_files():
    return skill_markdown_files(SKILLS_ROOT)


@pytest.mark.xfail(strict=False, reason="skills migrate on phase/canon-skills")
@pytest.mark.parametrize("skill_file", _skill_files(), ids=lambda p: str(p.relative_to(SKILLS_ROOT)))
def test_skill_invocations_are_permitted_by_schemas(skill_file):
    violations = check_skill_text(skill_file.read_text(), DEFS)
    assert not violations, (
        f"{skill_file.relative_to(SKILLS_ROOT)} instructs an operation the schema modules "
        "do not permit:\n" + "\n".join(f"  - {v}" for v in violations)
    )


def _violations(command: str) -> list[str]:
    return check_skill_text(f"```bash\n{command}\n```\n", DEFS)


def test_extractor_finds_canon_invocations():
    found = extract_invocations("```bash\ncanon list --type plan:phase\ncanon get --id x\n```")
    assert [inv["subcommand"] for inv in found] == ["list", "get"]


def test_extractor_accepts_a_valid_create():
    payload = '{"title": "t", "ordinal": 1, "effort": "e"}'
    assert _violations(f"canon create --type plan:milestone --subject m --payload '{payload}'") == []


def test_extractor_rejects_unknown_type():
    assert _violations("canon list --type project:phase")


def test_extractor_rejects_old_adaptive_commands():
    assert _violations("canon capture --bundle x")
    assert _violations("canon contradict --type aff:finding --id x")


def test_extractor_rejects_rel_flag():
    assert _violations("canon create --type plan:work-item --subject s --rel depends_on:rec-1")


def test_extractor_rejects_bad_transition():
    assert _violations("canon update --type plan:work-item --id x --transition done_late")
    assert _violations("canon update --type plan:work-item --id x --transition superseded")


def test_extractor_rejects_undeclared_payload_key():
    payload = '{"title": "t", "ordinal": 1, "effort": "e", "nonsense": 1}'
    assert _violations(f"canon create --type plan:milestone --subject m --payload '{payload}'")


def test_extractor_rejects_missing_required_key():
    assert _violations("canon create --type plan:milestone --subject m --payload '{\"title\": \"t\"}'")


def test_extractor_rejects_correct_on_current_type():
    assert _violations("canon correct --type plan:decision --id x")
    assert check_invocation({"subcommand": "correct", "type": "aff:check-run", "transition": None,
                             "rels": [], "payload": None, "raw": ""}, DEFS) == []
