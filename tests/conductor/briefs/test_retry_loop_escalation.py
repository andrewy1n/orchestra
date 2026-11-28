from __future__ import annotations

import re
from pathlib import Path

SECTION = (
    Path(__file__).resolve().parents[3]
    / "orchestra"
    / "conductor"
    / "briefs"
    / "sections"
    / "retry-loop.md"
)


def _text() -> str:
    return re.sub(r"\s+", " ", SECTION.read_text())


def test_retry_loop_states_the_per_failure_budget() -> None:
    text = _text()
    assert "per distinct failure" in text
    assert "conductor:redispatch-attempt" in text
    assert "failing criterion id and its sorted failing node ids" in text


def test_retry_loop_keeps_the_fix_task_ceiling() -> None:
    assert "`retry_max_fix_tasks`: 3 fix work-items" in _text()


def test_retry_loop_escalates_a_repair_that_changes_a_requirement() -> None:
    text = _text()
    assert "changes a requirement" in text
    assert "blocking `retry:<task-slug>` question" in text


def test_retry_loop_escalates_a_repair_that_changes_a_public_contract_or_frozen_test() -> None:
    text = _text()
    assert "a public contract" in text
    assert "a frozen test" in text
    assert "instead of re-dispatching" in text
