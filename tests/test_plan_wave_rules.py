"""tasks records recipes and phase run facts while executor mode stays derived."""

from __future__ import annotations

import re

import helpers as h
from conftest import REPO_ROOT
from skill_extraction import extract_invocations

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


def test_executor_is_an_optional_override_and_approach_stays_optional():
    work_item = _work_item_def()
    assert work_item["payload_enum"]["executor"] == ["inline", "subagent"]
    assert "executor" in work_item["payload"]
    assert "executor" in work_item["optional_payload"]
    assert "Approach" not in work_item["required_sections"]

    raw = h.skill_text("tasks")
    text = _flat(raw)
    assert "Dispatch derives the executor from the wave and project settings." in text
    assert (
        "Omit `executor` unless the plan needs an explicit `inline` or `subagent` override."
        in _flat(raw)
    )
    payloads = _work_item_payloads(raw)
    assert payloads
    assert all("executor" not in payload for payload in payloads)
    for inv in extract_invocations(raw):
        if inv["subcommand"] == "create" and inv["type"] == "score:work-item":
            assert "## Approach" in inv["raw"]
            assert "implementation recipe" in inv["raw"]
        for part in inv["records"] or []:
            if part.get("type") == "score:work-item":
                assert "## Approach" in part["body"]
                assert "implementation recipe" in part["body"]


def test_derived_wave_mode_and_explicit_overrides_use_one_executor():
    brief = _flat(_text("tasks"))
    assert "Dispatch derives the executor from wave size, estimates, and project settings." in brief
    assert "Omit `executor` unless the plan needs an explicit `inline` or `subagent` override." in brief
    assert "Explicit overrides in one wave must agree." in brief
    for path in (
        REPO_ROOT / "orchestra/conductor/briefs/sections/kinds-and-focus.md",
        REPO_ROOT / "README.md",
    ):
        doc = _flat(path.read_text())
        assert "Dispatch derives" in doc
        assert "Every task in a wave uses the same executor." in doc
        assert "explicit" in doc.lower()


def test_phase_body_records_size_stops_and_collision_notes():
    text = _flat(_text("tasks"))
    assert (
        "Phase body records session shape (`one sitting` | `more than one`), human stops, collision notes"
        in text
    )


def test_plan_review_stays_closed_until_recipe_executor_and_run_facts_are_present():
    text = _text("tasks")
    flat = _flat(text)
    gate = "Open the plan review gate (skip incidental). Do not open until task recipes,"
    question = next(
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create" and inv["type"] == "score:continuity-question"
    )
    assert question["payload"]["blocking"] is True
    assert question["payload"]["scope"].startswith("plan-review:")
    question_at = flat.index("canon create --type score:continuity-question")
    gate_at = flat.index(gate)
    assert gate_at < question_at
    window = flat[gate_at:question_at]
    assert "task recipes" in window
    assert "wave executor choices" in window
    assert "written `executor` values are optional overrides" in window
    assert "phase run facts" in window
    assert "Landing" in window
