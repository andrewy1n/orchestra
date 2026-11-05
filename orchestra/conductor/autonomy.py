"""Set an effort's autonomy level and migrate the free-text autonomy constraints to it."""

from __future__ import annotations

from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import Record

LEVELS = ("gated", "auto-plan", "auto-phases")


class AutonomyError(RuntimeError):
    """The level or effort is not valid."""


@dataclass(frozen=True)
class Mapping:
    constraint_id: str
    constraint: str
    effort: str
    level: str


def classify(statement: str) -> str | None:
    text = " ".join(statement.lower().split())
    if text.startswith("retired:"):
        return None
    if "without asking" in text and ("next phase" in text or "promote" in text):
        return "auto-phases"
    if "plan-review" in text and "preauthorized" in text:
        return "auto-plan"
    return None


def _text(record: Record, key: str) -> str:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) else ""


def _goal(project: Project, effort: str) -> Record:
    found = [
        r
        for r in project.list("score:effort")
        if r["subject"] == effort and r["lifecycle_state"] != "superseded"
    ]
    if not found:
        raise AutonomyError(f"unknown effort {effort!r}")
    return max(found, key=lambda r: r["recorded_at"])


def set_autonomy(project: Project, effort: str, level: str) -> Record:
    if level not in LEVELS:
        raise AutonomyError(f"autonomy must be one of {', '.join(LEVELS)}")
    goal = _goal(project, effort)
    return project.supersede(goal["id"], record_type="score:effort", payload={"autonomy": level})[
        "record"
    ]


def plan_migration(project: Project) -> list[Mapping]:
    mappings: list[Mapping] = []
    for record in project.list("score:constraint"):
        if record["lifecycle_state"] != "active":
            continue
        level = classify(_text(record, "statement"))
        effort = _text(record, "effort")
        if level is not None and effort:
            mappings.append(Mapping(record["id"], record["subject"], effort, level))
    return sorted(mappings, key=lambda m: (m.effort, m.constraint))


def strongest(mappings: list[Mapping]) -> dict[str, str]:
    rank = {level: i for i, level in enumerate(LEVELS)}
    levels: dict[str, str] = {}
    for mapping in mappings:
        if mapping.effort not in levels or rank[mapping.level] > rank[levels[mapping.effort]]:
            levels[mapping.effort] = mapping.level
    return levels


def apply_migration(project: Project, mappings: list[Mapping]) -> dict[str, str]:
    levels = strongest(mappings)
    for effort, level in levels.items():
        current = _text(_goal(project, effort), "autonomy") or "gated"
        if current != level:
            set_autonomy(project, effort, level)
    for mapping in mappings:
        project.supersede(
            mapping.constraint_id,
            record_type="score:constraint",
            payload={
                "statement": (
                    f"Retired: replaced by the effort field autonomy={levels[mapping.effort]} "
                    f"on {mapping.effort}."
                )
            },
        )
    return levels
