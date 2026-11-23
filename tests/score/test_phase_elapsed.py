from __future__ import annotations

from orchestra.score.facts.elapsed import Elapsed, TimedTask, phase_elapsed


def _task(key: str, wave: int | None, executor: str, estimate: int | None) -> TimedTask:
    return TimedTask(key=key, wave=wave, estimate_minutes=estimate, executor=executor)


def test_phase_elapsed_sums_inline_waves_and_takes_longest_of_other_waves() -> None:
    tasks = [
        _task("in-a", 1, "inline", 10),
        _task("in-b", 1, "inline", 15),
        _task("sub-a", 2, "subagent", 10),
        _task("sub-b", 2, "subagent", 40),
        _task("sub-blank", 2, "subagent", None),
        _task("zero", 3, "inline", 0),
    ]
    assert phase_elapsed(tasks) == Elapsed(minutes=10 + 15 + 40, unset_estimates=1)


def test_phase_elapsed_counts_zero_as_an_estimate() -> None:
    assert phase_elapsed([_task("only-zero", 1, "subagent", 0)]) == Elapsed(0, 0)


def test_phase_elapsed_treats_a_task_without_a_wave_as_its_own_group() -> None:
    tasks = [_task("lone-a", None, "subagent", 10), _task("lone-b", None, "subagent", 40)]
    assert phase_elapsed(tasks) == Elapsed(50, 0)


def test_phase_elapsed_has_no_minutes_when_no_task_has_an_estimate() -> None:
    tasks = [_task("none-a", 1, "subagent", None), _task("none-b", 2, "inline", None)]
    assert phase_elapsed(tasks) == Elapsed(None, 2)


def test_phase_elapsed_of_no_tasks_has_no_minutes() -> None:
    assert phase_elapsed([]) == Elapsed(None, 0)


def test_phase_elapsed_counts_each_unset_estimate_in_an_estimated_wave() -> None:
    tasks = [
        _task("missing-a", 1, "inline", None),
        _task("missing-b", 1, "inline", None),
        _task("known", 1, "inline", 25),
    ]
    assert phase_elapsed(tasks) == Elapsed(25, 2)
