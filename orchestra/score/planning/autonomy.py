"""Set an effort's autonomy level and migrate the free-text autonomy constraints to it."""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.score.planning.effort import Effort, current_effort, current_efforts

LEVELS = ("gated", "auto-plan", "auto-phases")

Autonomy = Literal["gated", "auto-plan", "auto-phases"]


class AutonomyError(RuntimeError):
    """The level or effort is not valid."""


@dataclass(frozen=True)
class Mapping:
    constraint_id: str
    constraint: str
    effort: str
    level: str


_EXECUTE = re.compile(r"plan and execute each phase without asking")
_PROMOTE = re.compile(
    r"plan and promote each next phase without asking(?: once the current one closes)?"
)
_STOPS = (
    re.compile(
        r"stop (?:only )?for failures, needs-human findings,? (?:pushes, and merges|or a push or merge)"
    ),
    re.compile(r"(?:pr )?merges? (?:still )?(?:needs?|requires?) (?:user )?approval"),
)
_MENTIONS = ("preauthorized", "pre-authorized", "without asking", "automatically execute")


def _gate(effort: str) -> re.Pattern[str]:
    named = rf"(?:{re.escape(effort.lower())} )?" if effort else ""
    scope = rf"(?: for (?:every|each|all) {named}phases?)?"
    return re.compile(rf"plan-review gates?{scope} (?:are|is) pre-?authorized(?: by the user)?")


def _clauses(statement: str) -> list[str]:
    text = " ".join(statement.lower().replace("\u2019", "'").split())
    return [part.strip() for part in re.split(r"[;.]", text) if part.strip()]


def classify(statement: str, effort: str = "") -> str | None:
    gate_pattern = _gate(effort)
    promote = gate = False
    for clause in _clauses(statement):
        if _PROMOTE.fullmatch(clause):
            promote = True
        elif gate_pattern.fullmatch(clause) or _EXECUTE.fullmatch(clause):
            gate = True
        elif not any(stop.fullmatch(clause) for stop in _STOPS):
            return None
    if promote:
        return "auto-phases"
    return "auto-plan" if gate else None


def mentions_autonomy(statement: str) -> bool:
    text = " ".join(statement.lower().split())
    return not text.startswith("retired:") and any(word in text for word in _MENTIONS)


def _text(record: Record, key: str) -> str:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) else ""


def _effort(project: Project, effort: str) -> Effort:
    found = current_effort(project.records(), effort)
    if found is None:
        raise AutonomyError(f"unknown effort {effort!r}")
    return found


def set_autonomy(project: Project, effort: str, level: str) -> Record:
    if level not in LEVELS:
        raise AutonomyError(f"autonomy must be one of {', '.join(LEVELS)}")
    goal = _effort(project, effort)
    if (goal.autonomy or "gated") == level:
        return goal.record
    return project.supersede(goal.id, record_type="score:effort", payload={"autonomy": level})[
        "record"
    ]


def resolve_effort(record: Record, known: Collection[str]) -> str:
    fields = (
        ("effort", "applies_to") if record["record_type"] == "score:constraint" else ("effort",)
    )
    for field in fields:
        value = _text(record, field)
        if value in known:
            return value
    return ""


def plan_migration(project: Project) -> tuple[list[Mapping], list[str]]:
    known = current_efforts(project.records())
    mappings: list[Mapping] = []
    notes: list[str] = []
    for record in project.list("score:constraint"):
        if record["lifecycle_state"] != "active":
            continue
        statement = _text(record, "statement")
        effort = resolve_effort(record, known)
        level = classify(statement, effort)
        subject = record["subject"]
        if level is None:
            if mentions_autonomy(statement):
                notes.append(
                    f"{subject}: mentions autonomy but is not a recognised grant; left alone"
                )
        elif effort:
            mappings.append(Mapping(record["id"], subject, effort, level))
        else:
            notes.append(f"{subject}: grants autonomy but covers no known effort; left alone")
    return sorted(mappings, key=lambda m: (m.effort, m.constraint)), sorted(notes)


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
        current = _effort(project, effort).autonomy or "gated"
        if LEVELS.index(level) > LEVELS.index(current):
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


@dataclass(frozen=True)
class MigrationReport:
    mappings: list[Mapping]
    notes: list[str]
    applied: bool
    levels: dict[str, str]


def migrate(project: Project, *, apply: bool) -> MigrationReport:
    mappings, notes = plan_migration(project)
    levels = apply_migration(project, mappings) if apply else {}
    return MigrationReport(mappings, notes, apply, levels)


def effort_autonomy(records: list[Record], effort: str) -> Autonomy:
    current = current_effort(records, effort)
    level = current.autonomy if current is not None else None
    return level or "gated"
