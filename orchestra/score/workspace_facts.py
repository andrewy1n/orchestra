from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import JsonObject, Record

DESIGN_TYPE = "score:design"
MILESTONE_TYPE = "score:milestone"
POSITION_TYPE = "score:position"
CONSTRAINT_TYPE = "score:constraint"
CONTINUITY_QUESTION_TYPE = "score:continuity-question"


@dataclass(frozen=True)
class DecisionFacts:
    phase: str
    choice: str
    alternatives: str


@dataclass(frozen=True)
class ConstraintFacts:
    applies_to: str
    statement: str


@dataclass(frozen=True)
class EffortSummary:
    goal: str
    kind: str


def _text(payload: JsonObject, key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def decision_facts(record: Record) -> DecisionFacts:
    payload = record_payload(record)
    return DecisionFacts(
        phase=_text(payload, "phase"),
        choice=_text(payload, "choice"),
        alternatives=_text(payload, "alternatives"),
    )


def constraint_facts(record: Record) -> ConstraintFacts:
    payload = record_payload(record)
    return ConstraintFacts(
        applies_to=_text(payload, "applies_to"), statement=_text(payload, "statement")
    )


def effort_summary(record: Record) -> EffortSummary:
    payload = record_payload(record)
    return EffortSummary(goal=_text(payload, "goal"), kind=_text(payload, "kind"))


def work_item_efforts(tasks: Iterable[Record]) -> dict[str, tuple[str, str]]:
    """Map each work-item id, and its first subject, to `(effort, subject)`."""
    found: dict[str, tuple[str, str]] = {}
    for task in tasks:
        entry = (_text(record_payload(task), "effort"), task["subject"])
        found[task["id"]] = entry
        found.setdefault(task["subject"], entry)
    return found


def effort_positions(records: Sequence[Record]) -> dict[str, str]:
    """Map effort subject to the position text of its active, open, effort-scoped position."""
    positions: dict[str, str] = {}
    for record in records:
        payload = record_payload(record)
        if (
            record["lifecycle_state"] == "active"
            and payload.get("status") != "closed"
            and payload.get("scope") == "effort"
        ):
            positions[record["subject"]] = _text(payload, "position")
    return positions
