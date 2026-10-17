"""Retry loop: re-dispatch, amendments, attempts, fix tasks, budget, next: plan."""

from __future__ import annotations

import json
import re

from conftest import REPO_ROOT
from skill_extraction import extract_invocations

SKILLS = REPO_ROOT / "skills"


def _text(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text()


def _flat(name: str) -> str:
    return re.sub(r"\s+", " ", _text(name))


def _work_item() -> dict:
    design = json.loads((REPO_ROOT / "contract" / "project-design.json").read_text())
    return next(record for record in design["records"] if record["name"] == "work-item")


def test_attempts_is_optional_on_work_item():
    work_item = _work_item()
    assert "attempts" in work_item["payload"]
    assert "attempts" in work_item["optional_payload"]
    assert "attempts" not in (work_item.get("payload_enum") or {})


def test_execute_phase_redispatch_selects_in_progress_before_planned():
    text = _text("execute-phase")
    flat = _flat("execute-phase")
    assert "--state in_progress" in text
    assert "before" in flat and "planned" in flat
    assert "next: execute" in flat or "`next` `execute`" in flat or "next` `execute`" in flat
    assert "result: fail" in flat or "`result` `fail`" in flat or "result` `fail`" in flat
    assert "same executor" in flat or "same `payload.executor`" in flat
    step2 = text.index("2. Select")
    retry_at = text.lower().index("in_progress")
    # Retry selection is documented at or before planned ready selection.
    assert retry_at < step2 or "before selecting" in flat or "before planned" in flat


def test_redispatch_records_assignment_amendment_with_failure_evidence():
    text = _text("execute-phase")
    flat = _flat("execute-phase")
    assert "assignment-amendment" in text
    assert "## Correction" in text
    assert "check-run" in flat
    assert "## Reason" in text or "assessment" in flat and "Reason" in text
    amendments = [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create" and inv["type"] == "project:assignment-amendment"
    ]
    assert amendments
    # At least one amendment example quotes failure evidence in the body template.
    assert any(
        "Correction" in (inv.get("raw") or "")
        and ("check-run" in (inv.get("raw") or "") or "fail" in (inv.get("raw") or "").lower())
        for inv in amendments
    )


def test_redispatch_increments_attempts():
    text = _text("execute-phase")
    flat = _flat("execute-phase")
    assert "attempts" in flat
    updates = [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "update"
        and inv["type"] == "project:work-item"
        and "attempts" in (inv.get("payload") or {})
    ]
    assert updates, "execute-phase must document incrementing payload attempts on re-dispatch"


def test_fix_task_depends_on_and_no_reopen_done():
    text = _text("execute-phase")
    flat = _flat("execute-phase")
    assert "fix" in flat and "work-item" in flat
    assert "depends_on" in flat
    assert "never reopen" in flat or "never transition" in flat and "`done`" in flat
    assert "done` work-items are never" in flat or "never reopen `done`" in flat or (
        "never" in flat and "`done`" in flat and ("reopen" in flat or "transition" in flat)
    )
    creates = [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create" and inv["type"] == "project:work-item"
    ]
    assert creates, "execute-phase must create a fix work-item"
    assert "update --rel" in text or any(
        inv.get("rel") or "depends_on" in (inv.get("raw") or "")
        for inv in extract_invocations(text)
        if inv["type"] == "project:work-item"
    )


def test_budget_defaults_overrides_and_exhaustion():
    text = _text("execute-phase")
    flat = _flat("execute-phase")
    assert "2 re-dispatch" in flat or "2 redispatches" in flat or "default: 2" in flat
    assert "2×" in text or "2x" in flat or "2 ×" in flat or "time multiplier" in flat
    assert "3 fix" in flat or "fix tasks" in flat and "3" in flat
    assert "run fact" in flat or "run-fact" in flat or "## Run facts" in text
    assert "retry_max_redispatches" in text
    assert "retry_time_multiplier" in text
    assert "retry_max_fix_tasks" in text
    assert "scope: retry:" in flat or '`scope` `retry:' in flat or "retry:<task-slug>" in flat
    assert "`needs` `human`" in flat or '"needs":"human"' in text or "needs: human" in flat
    questions = [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create"
        and inv["type"] == "project:continuity-question"
        and "retry:" in str(inv.get("payload") or {})
    ]
    assert questions
    findings = [
        inv
        for inv in extract_invocations(text)
        if inv["subcommand"] == "create"
        and inv["type"] == "project:finding"
        and (inv.get("payload") or {}).get("needs") == "human"
    ]
    assert findings
    # Clear documented next to the gate.
    assert any(
        inv["subcommand"] == "update"
        and inv["type"] == "project:continuity-question"
        and inv["transition"] == "answered"
        for inv in extract_invocations(text)
    )
    assert "stop" in flat and ("dispatch" in flat or "selecting" in flat)
    assert "evidence ladder" in flat or "evidence-escalation" in flat


def test_plan_phase_consumes_next_plan():
    text = _text("plan-phase")
    flat = _flat("plan-phase")
    assert "next: plan" in flat or "`next` `plan`" in flat or "next` `plan`" in flat
    assert "missing task" in flat or "missing work-item" in flat
    assert "plan-review" in flat
    assert any(
        inv["subcommand"] == "create"
        and inv["type"] == "project:continuity-question"
        and "plan-review:" in str(inv.get("payload") or {})
        for inv in extract_invocations(text)
    )


def test_verify_work_notes_parent_redispatch_without_changing_ladder():
    text = _text("verify-work")
    flat = _flat("verify-work")
    assert "re-dispatch" in flat or "redispatch" in flat or "execute-phase" in flat
    assert "fix" in flat and ("work-item" in flat or "task" in flat)
    assert "Decision evidence-escalation." in text
    assert "Do not use a failure count." in flat
