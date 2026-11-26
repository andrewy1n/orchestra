"""Pure policy for choosing a task wave executor."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from orchestra.canon.project_config import (
    DEFAULT_LONE_TASK_INLINE_MINUTES,
    DEFAULT_SMALL_WAVE_BUDGET_MINUTES,
)
from orchestra.score.planning.plan_shape import SIZE_BANDS

Executor = Literal["inline", "subagent"]
TaskSize = Literal["XS", "S", "M", "L", "XL"]
_SMALL_SIZES = ("XS", "S")


class ExecutorWaveError(ValueError):
    """A wave does not have one valid executor policy."""


@dataclass(frozen=True)
class ExecutorTask:
    subject: str
    size: str | None = None
    estimate_minutes: int | None = None
    executor: str | None = None
    assignee: str | None = None


def task_executor(
    task: ExecutorTask,
    wave_tasks: Sequence[ExecutorTask] | None = None,
    *,
    small_wave_budget_minutes: int = DEFAULT_SMALL_WAVE_BUDGET_MINUTES,
    lone_task_inline_minutes: int = DEFAULT_LONE_TASK_INLINE_MINUTES,
) -> Executor:
    """Return the dispatched executor, override, or prediction for the task wave."""
    if task.assignee in ("inline", "subagent"):
        return task.assignee
    return wave_executor(
        wave_tasks or [task],
        small_wave_budget_minutes=small_wave_budget_minutes,
        lone_task_inline_minutes=lone_task_inline_minutes,
    )


def wave_executor(
    tasks: Sequence[ExecutorTask],
    *,
    small_wave_budget_minutes: int = DEFAULT_SMALL_WAVE_BUDGET_MINUTES,
    lone_task_inline_minutes: int = DEFAULT_LONE_TASK_INLINE_MINUTES,
) -> Executor:
    """Choose one executor for a wave, honoring assignments and explicit overrides."""
    if not tasks:
        raise ExecutorWaveError("cannot choose an executor for an empty wave")
    if type(small_wave_budget_minutes) is not int or small_wave_budget_minutes < 0:
        raise ExecutorWaveError("small-wave budget must be a non-negative integer")
    if type(lone_task_inline_minutes) is not int or lone_task_inline_minutes < 0:
        raise ExecutorWaveError("lone-task inline threshold must be a non-negative integer")

    fixed = [(task, _fixed_executor(task)) for task in tasks]
    assigned = [(task, executor) for task, executor in fixed if executor is not None]
    if assigned:
        modes = {executor for _, executor in assigned}
        if len(modes) > 1:
            detail = ", ".join(f"{task.subject}={executor}" for task, executor in assigned)
            raise ExecutorWaveError(f"tasks disagree on executor: {detail}")
        executor = assigned[0][1]
        if executor == "inline":
            return "inline"
        if executor == "subagent":
            return "subagent"

    if len(tasks) == 1:
        return _single_task_prediction(tasks[0], lone_task_inline_minutes)
    if all(_size(task.size) in _SMALL_SIZES for task in tasks):
        total = sum(_estimate(task) for task in tasks)
        if total <= small_wave_budget_minutes:
            return "inline"
    return "subagent"


def _fixed_executor(task: ExecutorTask) -> Executor | None:
    if task.assignee == "inline":
        return "inline"
    if task.assignee == "subagent":
        return "subagent"
    if task.executor and task.executor not in ("inline", "subagent"):
        raise ExecutorWaveError(f"unknown executor on: {task.subject}")
    if task.executor == "inline":
        return "inline"
    if task.executor == "subagent":
        return "subagent"
    return None


def _single_task_prediction(task: ExecutorTask, lone_task_inline_minutes: int) -> Executor:
    if task.estimate_minutes is None:
        return "subagent"
    return "inline" if _estimate(task) <= lone_task_inline_minutes else "subagent"


def _size(value: str | None) -> TaskSize:
    if value is None:
        return "M"
    if value == "XS" or value == "S" or value == "M" or value == "L" or value == "XL":
        return value
    raise ExecutorWaveError(f"unknown task size: {value}")


def _estimate(task: ExecutorTask) -> int:
    if task.estimate_minutes is None:
        return SIZE_BANDS[_size(task.size)][1]
    if type(task.estimate_minutes) is not int or task.estimate_minutes < 0:
        raise ExecutorWaveError(f"invalid estimate for task {task.subject!r}")
    return task.estimate_minutes
