from __future__ import annotations

from conftest import REPO_ROOT


def _flat(text: str) -> str:
    return " ".join(text.split())


def _section(name: str) -> str:
    path = REPO_ROOT / "orchestra" / "conductor" / "briefs" / "sections" / f"{name}.md"
    return _flat(path.read_text())


def test_planning_guidance_omits_executor_from_default_work_items() -> None:
    shape = _section("task-shapes")

    assert '"executor"' not in shape
    assert "Omit `executor` unless the plan needs an explicit" in shape


def test_executor_guidance_preserves_overrides_and_wave_consistency() -> None:
    kinds = _section("kinds-and-focus")
    planning = _section("planning-mechanics")
    records = _section("record-mechanics")

    assert "optional `inline` or" in kinds
    assert "overrides in one wave must agree." in kinds
    assert "Every task in a wave uses the same executor." in kinds
    assert "A written `executor` is an" in planning
    assert "Add `executor` only for an explicit" in records


def test_execution_and_retry_guidance_use_derived_mode() -> None:
    execute = _section("execute-dispatch")
    retry = _section("retry-loop")

    assert "Use the resolved mode for every task in the wave." in execute
    assert "keep the mode resolved for the task's first dispatch." in retry


def test_plan_review_guidance_does_not_require_written_executors() -> None:
    planning = _section("planning-mechanics")
    tasks = _section("tasks-process")

    assert "wave executors agree" not in planning
    assert "Executor choices derive from wave shape and project settings" in tasks
    assert "written `executor` values are optional" in tasks
