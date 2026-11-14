from __future__ import annotations

import helpers as h
from conftest import REPO_ROOT


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_planning_guidance_omits_executor_from_default_work_items() -> None:
    tasks = h.skill_text("tasks")
    shape = (REPO_ROOT / "skills" / "tasks" / "references" / "task-shapes.md").read_text()

    assert "Write `executor` only when the plan needs an explicit" in _flat(tasks)
    assert '"executor"' not in shape
    assert "Omit `executor` unless the plan needs an explicit" in shape


def test_executor_guidance_preserves_overrides_and_wave_consistency() -> None:
    kinds = (REPO_ROOT / "shared" / "kinds-and-focus.md").read_text()
    planning = (REPO_ROOT / "shared" / "planning-mechanics.md").read_text()
    records = (REPO_ROOT / "shared" / "record-mechanics.md").read_text()

    assert "optional `inline` or" in kinds
    assert "overrides in one wave must agree." in kinds
    assert "Every task in a wave uses the same executor." in kinds
    assert "A written `executor` is an" in planning
    assert "Add `executor` only for an explicit" in records


def test_execution_and_retry_guidance_use_derived_mode() -> None:
    execute = (REPO_ROOT / "shared" / "execute-mechanics.md").read_text()
    retry = (REPO_ROOT / "shared" / "retry-loop.md").read_text()

    assert "Use the executor mode resolved by `orchestra wave start`." in execute
    assert "Dispatch with the mode resolved for the wave." in execute
    assert (
        "Re-dispatch with the same executor mode selected for the task's first dispatch." in retry
    )
    assert '"executor"' not in retry


def test_plan_review_guidance_does_not_require_written_executors() -> None:
    planning = (REPO_ROOT / "shared" / "planning-mechanics.md").read_text()
    tasks = (REPO_ROOT / "skills" / "tasks" / "SKILL.md").read_text()

    assert "wave executors agree" not in planning
    assert "wave executor choices" not in tasks
    assert "written `executor` values are optional" in _flat(tasks)
