from __future__ import annotations

import pytest

from orchestra.score.planning.executor import (
    SIZE_BANDS,
    ExecutorTask,
    ExecutorWaveError,
    task_executor,
    wave_executor,
)


@pytest.mark.parametrize("size", ["XS", "S", "M", None])
def test_r2_single_task_up_to_medium_runs_inline(size: str | None) -> None:
    assert wave_executor([ExecutorTask("small", size=size, estimate_minutes=5)]) == "inline"


@pytest.mark.parametrize("size", ["L", "XL"])
def test_r3_large_single_task_runs_as_subagent(size: str) -> None:
    assert wave_executor([ExecutorTask("large", size=size)]) == "subagent"


def test_r4_small_wave_runs_inline_at_budget_boundary() -> None:
    tasks = [
        ExecutorTask("xs", size="XS", estimate_minutes=5),
        ExecutorTask("s", size="S", estimate_minutes=10),
    ]

    assert wave_executor(tasks) == "inline"


def test_r5_wave_above_budget_or_with_large_task_uses_subagents() -> None:
    above_budget = [
        ExecutorTask("xs", size="XS", estimate_minutes=6),
        ExecutorTask("s", size="S", estimate_minutes=10),
    ]
    mixed_size = [
        ExecutorTask("xs", size="XS", estimate_minutes=1),
        ExecutorTask("m", size="M", estimate_minutes=1),
    ]

    assert wave_executor(above_budget) == "subagent"
    assert wave_executor(mixed_size) == "subagent"


def test_r6_missing_size_counts_as_medium() -> None:
    assert wave_executor([ExecutorTask("small", size="XS"), ExecutorTask("unknown")]) == "subagent"


def test_r7_missing_estimate_uses_size_band_upper_bound() -> None:
    tasks = [ExecutorTask("s", size="S"), ExecutorTask("xs", size="XS", estimate_minutes=0)]

    assert SIZE_BANDS["S"][1] == 5
    assert wave_executor(tasks, small_wave_budget_minutes=5) == "inline"
    assert wave_executor(tasks, small_wave_budget_minutes=4) == "subagent"


def test_r8_default_small_wave_budget_is_fifteen_minutes() -> None:
    tasks = [
        ExecutorTask("xs-one", size="XS", estimate_minutes=7),
        ExecutorTask("xs-two", size="XS", estimate_minutes=8),
    ]

    assert wave_executor(tasks) == "inline"


def test_r9_configured_small_wave_budget_changes_wave_mode() -> None:
    tasks = [
        ExecutorTask("xs-one", size="XS", estimate_minutes=8),
        ExecutorTask("xs-two", size="XS", estimate_minutes=8),
    ]

    assert wave_executor(tasks, small_wave_budget_minutes=16) == "inline"
    assert wave_executor(tasks, small_wave_budget_minutes=15) == "subagent"


def test_r10_explicit_executor_overrides_prediction_for_whole_wave() -> None:
    tasks = [
        ExecutorTask("small", size="XS", executor="subagent"),
        ExecutorTask("large", size="L"),
    ]

    assert wave_executor(tasks) == "subagent"


def test_r11_conflicting_executor_overrides_name_tasks() -> None:
    tasks = [
        ExecutorTask("inline-task", executor="inline"),
        ExecutorTask("subagent-task", executor="subagent"),
    ]

    with pytest.raises(ExecutorWaveError, match=r"inline-task=inline.*subagent-task=subagent"):
        wave_executor(tasks)


def test_unknown_written_executor_is_rejected() -> None:
    with pytest.raises(ExecutorWaveError, match="unknown executor on: task"):
        wave_executor([ExecutorTask("task", size="XS", executor="worker")])


def test_r13_redispatch_keeps_first_executor_after_wave_changes() -> None:
    dispatched = ExecutorTask("first", size="XS", assignee="subagent")
    new_small_task = ExecutorTask("second", size="XS", estimate_minutes=1)

    assert task_executor(dispatched) == "subagent"
    assert wave_executor([dispatched, new_small_task]) == "subagent"


def test_lone_task_at_threshold_runs_inline() -> None:
    task = ExecutorTask("lone", size="M", estimate_minutes=10)

    assert wave_executor([task]) == "inline"


def test_lone_task_above_threshold_runs_as_subagent() -> None:
    task = ExecutorTask("lone", size="S", estimate_minutes=11)

    assert wave_executor([task]) == "subagent"


def test_lone_task_default_threshold_is_ten_minutes() -> None:
    from orchestra.canon.project_config import DEFAULT_LONE_TASK_INLINE_MINUTES

    assert DEFAULT_LONE_TASK_INLINE_MINUTES == 10
    task = ExecutorTask("lone", size="L", estimate_minutes=10)
    assert task_executor(task) == "inline"


def test_lone_task_keyword_moves_threshold() -> None:
    task = ExecutorTask("lone", size="S", estimate_minutes=5)

    assert wave_executor([task], lone_task_inline_minutes=4) == "subagent"
    assert wave_executor([task], lone_task_inline_minutes=5) == "inline"


def test_lone_task_override_subagent_beats_small_estimate() -> None:
    task = ExecutorTask("lone", size="XS", estimate_minutes=4, executor="subagent")

    assert wave_executor([task]) == "subagent"
    assert task_executor(task) == "subagent"


def test_lone_task_override_inline_beats_large_estimate() -> None:
    task = ExecutorTask("lone", size="XL", estimate_minutes=30, executor="inline")

    assert wave_executor([task]) == "inline"


@pytest.mark.parametrize("size", ["XS", "S", "M", "L", None])
def test_lone_task_without_estimate_runs_as_subagent(size: str | None) -> None:
    task = ExecutorTask("lone", size=size)

    assert wave_executor([task]) == "subagent"
    assert task_executor(task) == "subagent"


def test_lone_task_without_estimate_still_honors_a_written_executor() -> None:
    task = ExecutorTask("lone", size="M", executor="inline")

    assert wave_executor([task]) == "inline"


@pytest.mark.parametrize("value", [-1, True, 1.5, "10"])
def test_wave_executor_rejects_invalid_lone_task_threshold(value: object) -> None:
    task = ExecutorTask("lone", size="S", estimate_minutes=4)

    with pytest.raises(ExecutorWaveError, match="lone-task"):
        wave_executor([task], lone_task_inline_minutes=value)  # pyright: ignore[reportArgumentType]
