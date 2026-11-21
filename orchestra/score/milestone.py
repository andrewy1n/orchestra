from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import Record


@dataclass(frozen=True)
class MilestoneFacts:
    id: str
    subject: str
    title: str
    ordinal: int


def milestone_facts(record: Record) -> MilestoneFacts:
    payload = record_payload(record)
    title = payload.get("title")
    ordinal = payload.get("ordinal")
    return MilestoneFacts(
        id=record["id"],
        subject=record["subject"],
        title=title if isinstance(title, str) and title else record["subject"],
        ordinal=ordinal if type(ordinal) is int else 0,
    )


def milestone_state(phase_states: Sequence[str]) -> str:
    if any(state == "in_progress" for state in phase_states):
        return "in_progress"
    if phase_states and all(state == "done" for state in phase_states):
        return "done"
    return "planned"
