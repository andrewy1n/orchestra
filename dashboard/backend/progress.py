"""Phase progress stages for the hub cards."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass

FULL_STAGES = ("spec", "design", "tasks", "execute", "verify", "review", "land", "close")
LIGHT_STAGES = FULL_STAGES[2:]


@dataclass(frozen=True)
class Stage:
    id: str
    state: str


def derive_stages(
    *,
    weight: str,
    phase_state: str,
    approved: Collection[str],
    task_states: Sequence[str],
    requirement_statuses: Sequence[str],
    review_passed_at_head: bool,
    branch_merged: bool,
) -> list[Stage]:
    done = {
        "spec": "spec" in approved,
        "design": "design" in approved,
        "tasks": "plan" in approved,
        "execute": bool(task_states) and all(state == "done" for state in task_states),
        "verify": all(status == "verified" for status in requirement_statuses),
        "review": review_passed_at_head,
        "land": branch_merged,
        "close": phase_state == "done",
    }
    ids = LIGHT_STAGES if weight == "light" else FULL_STAGES
    stages: list[Stage] = []
    current_found = False
    for stage_id in ids:
        if done[stage_id]:
            state = "done"
        elif not current_found:
            state = "current"
            current_found = True
        else:
            state = "pending"
        stages.append(Stage(stage_id, state))
    return stages
