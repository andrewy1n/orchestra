from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from orchestra.canon.types import Record
from orchestra.score.lookups import current_phase, current_phases


class WorkflowBlockerError(ValueError):
    pass


@dataclass(frozen=True)
class WorkflowBlocker:
    record: Record
    scope: Literal["phase", "effort"]
    phase: str | None


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
        record_type = record["record_type"]
        if record_type == "tuner:finding":
            if _payload_text(record, "needs") != "human" or record["lifecycle_state"] in (
                "refuted",
                "retracted",
            ):
                continue
            record_effort = _payload_text(record, "effort")
        elif record_type == "score:continuity-question":
            if payload.get("blocking") is not True or record["lifecycle_state"] != "open":
                continue
            record_effort = record["subject"]
        else:
            continue
        owned_phase = payload.get("phase")
        if owned_phase is None:
            if record_effort == effort:
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
            blockers.append(WorkflowBlocker(record, "phase", owned_phase))
    return blockers
