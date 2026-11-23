from __future__ import annotations

import pytest

from orchestra.score.planning.executor import (
    SIZE_BANDS,
    ExecutorTask,
    ExecutorWaveError,
    task_executor,
    wave_executor,
)


@pytest.mark.parametrize("size", ["XS", "S"])
def test_r2_small_single_task_runs_inline(size: str) -> None:
    assert wave_executor([ExecutorTask("small", size=size)]) == "inline"


@pytest.mark.parametrize("size", ["M", "L", "XL", None])
def test_r3_large_or_unsized_single_task_runs_as_subagent(size: str | None) -> None:
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

    assert SIZE_BANDS["S"][1] == 10
    assert wave_executor(tasks, small_wave_budget_minutes=10) == "inline"
    assert wave_executor(tasks, small_wave_budget_minutes=9) == "subagent"


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
