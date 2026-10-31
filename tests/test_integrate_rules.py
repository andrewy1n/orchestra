"""execute-phase records semantic integration and does not treat a git merge as pass."""

from __future__ import annotations

import re

import helpers as h
from conftest import REPO_ROOT
from skill_extraction import check_skill_text, extract_invocations

SKILL = REPO_ROOT / "skills" / "execute-phase" / "SKILL.md"


def _text() -> str:
    return re.sub(r"\s+", " ", h.skill_text("execute-phase"))


def _integration_creates(text: str) -> list[dict]:
    return [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create" and inv["type"] == "conductor:integration-report"
    ]


def test_integration_report_create_matches_the_contract(resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    text = h.skill_text("execute-phase")
    violations = check_skill_text(text, defs)
    assert not violations, "\n".join(violations)

    creates = _integration_creates(text)
    assert len(creates) == 1
    record = defs["conductor:integration-report"]
    payload = creates[0]["payload"]
    required = set(record["payload"]) - {"subject"} - set(record.get("optional_payload") or [])
    assert required <= set(payload)
    documented = payload["result"].strip("<>").split("|")
    assert documented == record["payload_enum"]["result"]
    for section in record["required_sections"]:
        assert f"## {section}" in creates[0]["raw"]


def test_a_git_merge_is_not_a_pass():
    text = _text()
    assert (
        "`pass` only when verdict is `PASS` and those sections hold — a clean git merge is not enough."
        in text
    )
    assert "Write integration-report `pass` from a clean git merge alone" in text


def test_integration_report_is_skipped_for_incidental_and_serial_waves():
    text = _text()
    assert "Skip when incidental or no multi-task implementation wave." in text
    assert "One `conductor:integration-report` from the reviewer's `integration` map." in text
