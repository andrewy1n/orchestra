from __future__ import annotations

from collections.abc import Sequence

from orchestra.canon.types import Record
from orchestra.score.facts.work_item_facts import record_scope
from orchestra.score.lookups import LIVE_WORK_ITEM_STATES, owning_work_item, record_order
from orchestra.score.planning.effort import record_effort
from orchestra.tuner.record_facts import CheckRunFacts, check_run_facts

_INACTIVE = ("superseded", "retracted")


def _belongs(record: Record, task: Record, work_items: Sequence[Record]) -> bool:
    phase = record_scope(task).phase
    candidates = [
        item
        for item in work_items
        if item["id"] == task["id"]
        or (item["lifecycle_state"] in LIVE_WORK_ITEM_STATES and record_scope(item).phase == phase)
    ]
    owner = owning_work_item(record["subject"], candidates)
    if owner is None or owner["id"] != task["id"]:
        return False
    own = record_effort(record)
    return own is None or own == (record_effort(task) or "")


def _latest_runs(checks: Sequence[Record]) -> dict[str, CheckRunFacts]:
    latest: dict[str, CheckRunFacts] = {}
    for record in sorted(checks, key=record_order):
        if record["lifecycle_state"] in _INACTIVE:
            continue
        facts = check_run_facts(record)
        latest[facts.criterion_id] = facts
    return latest


def _task_awaits(
    task: Record,
    work_items: Sequence[Record],
    acceptances: Sequence[Record],
    latest: dict[str, CheckRunFacts],
) -> bool:
    mine = [
        record
        for record in acceptances
        if record["lifecycle_state"] not in _INACTIVE and _belongs(record, task, work_items)
    ]
    runs = [latest.get(record["id"]) for record in mine]
    if not mine or any(run is None or run.result != "pass" for run in runs):
        return False
    return any(run is not None and run.method == "manual" and not run.signed_by for run in runs)


def awaiting_signoff(
    phase_state: str,
    members: Sequence[Record],
    work_items: Sequence[Record],
    acceptances: Sequence[Record],
    checks: Sequence[Record],
) -> bool:
    open_tasks = [task for task in members if task["lifecycle_state"] != "done"]
    if phase_state == "done" or not open_tasks:
        return False
    latest = _latest_runs(checks)
    return all(_task_awaits(task, work_items, acceptances, latest) for task in open_tasks)
