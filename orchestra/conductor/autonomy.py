"""Set an effort's autonomy level and migrate the free-text autonomy constraints to it."""

from __future__ import annotations

import re
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


def _known_efforts(project: Project) -> set[str]:
    return {
        r["subject"] for r in project.list("score:effort") if r["lifecycle_state"] != "superseded"
    }


def resolve_effort(record: Record, known: set[str]) -> str:
    for field in ("effort", "applies_to"):
        value = _text(record, field)
        if value in known:
            return value
    suffixes = [e for e in known if record["subject"] == e or record["subject"].endswith("-" + e)]
    return max(suffixes, key=len) if suffixes else ""


def plan_migration(project: Project) -> tuple[list[Mapping], list[str]]:
    known = _known_efforts(project)
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
        current = _text(_goal(project, effort), "autonomy") or "gated"
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
