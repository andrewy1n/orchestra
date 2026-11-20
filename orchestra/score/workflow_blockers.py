from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from orchestra.canon.types import Record
from orchestra.score.lookups import (
    check_run_criteria,
    corrected_ids,
    current_phase,
    current_phases,
    dependencies,
    latest_record,
    live_work_items,
)


class WorkflowBlockerError(ValueError):
    pass


@dataclass(frozen=True)
class WorkflowBlocker:
    record: Record
    scope: Literal["task", "phase", "effort"]
    phase: str | None
    task: str | None = None


HumanGateKind = Literal["blocking-question", "open-question", "needs-human", "unsigned-check"]


@dataclass(frozen=True)
class HumanGate:
    kind: HumanGateKind
    record: Record
    clears: str


OPEN_FINDING_STATES = ("asserted", "supported", "disputed")
CHECK_RUN_TYPE = "tuner:check-run"
QUESTION_TYPE = "score:continuity-question"
FINDING_TYPE = "tuner:finding"
CLEARS: dict[str, str] = {
    "blocking-question": QUESTION_TYPE,
    "open-question": QUESTION_TYPE,
    "needs-human": FINDING_TYPE,
    "unsigned-check": CHECK_RUN_TYPE,
}


def is_open_finding(record: Record) -> bool:
    return (
        record["record_type"] == FINDING_TYPE
        and _payload_text(record, "needs") == "human"
        and record["lifecycle_state"] in OPEN_FINDING_STATES
    )


def _is_open_question(record: Record) -> bool:
    return record["record_type"] == QUESTION_TYPE and record["lifecycle_state"] == "open"


def _is_blocking_question(record: Record) -> bool:
    return _is_open_question(record) and record["payload"].get("blocking") is True


def _uncorrected_manual_checks(records: list[Record]) -> list[Record]:
    corrected = corrected_ids(records)
    return [
        record
        for record in records
        if record["record_type"] == CHECK_RUN_TYPE
        and _payload_text(record, "method") == "manual"
        and record["id"] not in corrected
    ]


def is_signed(run: Record) -> bool:
    return bool(_payload_text(run, "signed_by").strip())


def _latest_among(acceptance: Record, runs: list[Record]) -> Record | None:
    names = check_run_criteria(acceptance)
    return latest_record(run for run in runs if _payload_text(run, "criterion_id") in names)


def latest_manual_check(acceptance: Record, records: list[Record]) -> Record | None:
    return _latest_among(acceptance, _uncorrected_manual_checks(records))


def unsigned_manual_checks(records: list[Record]) -> list[Record]:
    runs = _uncorrected_manual_checks(records)
    claimed: set[str] = set()
    latest_runs: list[Record] = []
    for acceptance in records:
        if acceptance["record_type"] != "score:acceptance":
            continue
        names = check_run_criteria(acceptance)
        owned = [run for run in runs if _payload_text(run, "criterion_id") in names]
        claimed.update(run["id"] for run in owned)
        deciding = latest_record(owned)
        if deciding is not None:
            latest_runs.append(deciding)
    unowned: dict[str, list[Record]] = {}
    for run in runs:
        if run["id"] not in claimed:
            unowned.setdefault(_payload_text(run, "criterion_id") or run["id"], []).append(run)
    latest_runs.extend(
        run for group in unowned.values() if (run := latest_record(group)) is not None
    )
    unsigned: list[Record] = []
    for run in latest_runs:
        if not is_signed(run) and run not in unsigned:
            unsigned.append(run)
    return unsigned


def human_gates(records: list[Record]) -> list[HumanGate]:
    gates: list[HumanGate] = []
    for record in records:
        if _is_blocking_question(record):
            gates.append(HumanGate("blocking-question", record, CLEARS["blocking-question"]))
        elif _is_open_question(record):
            gates.append(HumanGate("open-question", record, CLEARS["open-question"]))
        elif is_open_finding(record):
            gates.append(HumanGate("needs-human", record, CLEARS["needs-human"]))
    gates.extend(
        HumanGate("unsigned-check", run, CLEARS["unsigned-check"])
        for run in unsigned_manual_checks(records)
    )
    return gates


def _payload_text(record: Record, key: str) -> str:
    value = record["payload"].get(key)
    return value if isinstance(value, str) else ""


def _dependencies(record: Record) -> set[str]:
    value = record["payload"].get("depends_on", [])
    if not isinstance(value, list):
        raise WorkflowBlockerError(f"phase {record['subject']!r} has invalid dependencies")
    dependencies: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise WorkflowBlockerError(f"phase {record['subject']!r} has invalid dependencies")
        dependencies.add(item)
    return dependencies


def _phase_chain(records: list[Record], phase: Record) -> set[str]:
    phases = {
        subject: record
        for subject, record in current_phases(records).items()
        if _payload_text(record, "effort") == _payload_text(phase, "effort")
    }
    pending = [phase["subject"]]
    found: set[str] = set()
    while pending:
        subject = pending.pop()
        if subject in found:
            continue
        found.add(subject)
        current = phases.get(subject)
        if current is None:
            raise WorkflowBlockerError(f"unknown phase dependency {subject!r}")
        for dependency in _dependencies(current):
            target = current_phase(dependency, records)
            if target is None:
                raise WorkflowBlockerError(
                    f"phase {subject!r} depends on unknown phase {dependency!r}"
                )
            if _payload_text(target, "effort") != _payload_text(phase, "effort"):
                raise WorkflowBlockerError(
                    f"phase {subject!r} depends on phase {dependency!r} from another effort"
                )
            pending.append(dependency)
    return found


def phase_blockers(records: list[Record], phase_slug: str) -> list[WorkflowBlocker]:
    phase = current_phase(phase_slug, records)
    if phase is None:
        raise WorkflowBlockerError(f"phase {phase_slug!r} not found")
    effort = _payload_text(phase, "effort")
    chain = _phase_chain(records, phase)
    blockers: list[WorkflowBlocker] = []
    for record in records:
        payload = record["payload"]
        if is_open_finding(record):
            record_effort = _payload_text(record, "effort")
        elif _is_blocking_question(record):
            record_effort = record["subject"]
        else:
            continue
        scope = _payload_text(record, "scope") if record["record_type"] == QUESTION_TYPE else ""
        is_task_question = scope.startswith("task:")
        task = scope.removeprefix("task:")
        owned_phase = payload.get("phase")
        if owned_phase is None:
            if record_effort == effort:
                if is_task_question:
                    raise WorkflowBlockerError(
                        f"question {record['id']!r} needs a phase for task {task!r}"
                    )
                blockers.append(WorkflowBlocker(record, "effort", None))
            continue
        if not isinstance(owned_phase, str):
            raise WorkflowBlockerError(f"blocker {record['subject']!r} has invalid phase")
        owner = current_phase(owned_phase, records)
        if owner is None or _payload_text(owner, "effort") != record_effort:
            raise WorkflowBlockerError(
                f"blocker {record['subject']!r} has a phase from another effort or no phase"
            )
        if record_effort == effort and owned_phase in chain:
            if is_task_question and not any(
                item["subject"] == task for item in live_work_items(owned_phase, records)
            ):
                raise WorkflowBlockerError(
                    f"question {record['id']!r} holds unknown task {task!r} in phase {owned_phase!r}"
                )
            if is_task_question and owned_phase == phase_slug:
                blockers.append(WorkflowBlocker(record, "task", owned_phase, task))
            else:
                blockers.append(WorkflowBlocker(record, "phase", owned_phase))
    return blockers


def blocked_tasks(items: list[Record], blockers: list[WorkflowBlocker]) -> set[str]:
    blocked = {blocker.task for blocker in blockers if blocker.task is not None}
    if not blocked:
        return blocked
    dependents: dict[str, list[str]] = {}
    for item in items:
        for dependency in dependencies(item):
            dependents.setdefault(dependency, []).append(item["subject"])
    pending = list(blocked)
    while pending:
        for dependent in dependents.get(pending.pop(), []):
            if dependent not in blocked:
                blocked.add(dependent)
                pending.append(dependent)
    return blocked
