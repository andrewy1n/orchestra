"""plan-phase records the recipe, one shared wave executor, and phase run facts before plan review."""

from __future__ import annotations

import json
import re

import helpers as h
from conftest import REPO_ROOT
from skill_extraction import extract_invocations

SKILLS = REPO_ROOT / "skills"


def _text(name: str) -> str:
    return h.skill_text(name)


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _work_item_payloads(text: str) -> list[dict]:
    payloads = []
    for inv in extract_invocations(text):
        if inv["subcommand"] == "create" and inv["type"] == "score:work-item" and inv["payload"]:
            payloads.append(inv["payload"])
        for part in inv["records"] or []:
            if part.get("type") == "score:work-item":
                payloads.append(part["payload"])
    return payloads


def _work_item_def() -> dict:
    return h.record_def("work-item")


def test_executor_is_inline_or_subagent_and_approach_stays_optional():
    work_item = _work_item_def()
    assert work_item["payload_enum"]["executor"] == ["inline", "subagent"]
    assert "executor" in work_item["payload"]
    assert "executor" in work_item["optional_payload"]
    assert "Approach" not in work_item["required_sections"]

    raw = _text("plan-phase")
    text = _flat(raw)
    assert "`executor` (`inline`| `subagent`; missing → `subagent`; same within a wave)" in text
    payloads = _work_item_payloads(raw)
    assert payloads
    assert {payload["executor"] for payload in payloads} <= {"inline", "subagent"}
    for inv in extract_invocations(raw):
        if inv["subcommand"] == "create" and inv["type"] == "score:work-item":
            assert "## Approach" in inv["raw"]
            assert "implementation recipe" in inv["raw"]
        for part in inv["records"] or []:
            if part.get("type") == "score:work-item":
                assert "## Approach" in part["body"]
                assert "implementation recipe" in part["body"]


def test_every_task_in_a_wave_uses_the_same_executor():
    assert "same within a wave" in _flat(_text("plan-phase"))
    for path in (SKILLS / "kinds-and-focus.md", REPO_ROOT / "README.md"):
        doc = _flat(path.read_text())
        assert "`inline` or `subagent`" in doc
        assert "Every task in a wave uses the same executor." in doc
        assert "Missing `executor` means `subagent`." in doc
    executors = {payload["executor"] for payload in _work_item_payloads(_text("plan-phase"))}
    assert len(executors) == 1


def test_phase_body_records_size_stops_and_collision_notes():
    text = _flat(_text("plan-phase"))
    assert "Phase body records session shape (`one sitting` | `more than one`), human stops, collision notes" in text


def test_plan_review_stays_closed_until_recipe_executor_and_run_facts_are_present():
    text = _text("plan-phase")
    flat = _flat(text)
    gate = "Open the plan review gate (skip incidental). Do not open until:"
    question = next(
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create" and inv["type"] == "score:continuity-question"
    )
    assert question["payload"]["blocking"] is True
    assert question["payload"]["scope"].startswith("plan-review:")
    question_at = flat.rindex("canon create --type score:continuity-question")
    gate_at = flat.rindex(gate)
    assert gate_at < question_at
    window = flat[gate_at:question_at]
    assert "each work-item has `## Approach`" in window
    assert "wave executors agree" in window
    assert "phase body has size, human stops, collision notes" in window
