from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class TimedTask:
    key: str
    wave: int | None
    estimate_minutes: int | None
    executor: str | None


@dataclass(frozen=True)
class Elapsed:
    minutes: int | None
    unset_estimates: int


def phase_elapsed(tasks: Sequence[TimedTask]) -> Elapsed:
    """Wave-rule minutes: an inline wave sums its estimates, any other wave contributes its longest."""
    unset = sum(task.estimate_minutes is None for task in tasks)
    groups: dict[int | str, list[TimedTask]] = {}
    for task in tasks:
        groups.setdefault(task.wave if task.wave is not None else task.key, []).append(task)

    def order(key: int | str) -> tuple[int, int | str]:
        return (0, key) if isinstance(key, int) else (1, key)

    figures: list[int] = []
    for key in sorted(groups, key=order):
        members = groups[key]
        values = [task.estimate_minutes for task in members if task.estimate_minutes is not None]
        if not values:
            continue
        if all(task.executor == "inline" for task in members):
            figures.append(sum(values))
        else:
            figures.append(max(values))
    return Elapsed(sum(figures) if figures else None, unset)
