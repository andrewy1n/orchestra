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


_RESTRICTION = re.compile(
    r"\b(not|never|no|don't|cannot|can't|unless|except|forbid|forbidden)\b"
    r"|\bmust ask\b|\bask first\b|\bask before\b"
)
_SCOPED = re.compile(r"\bfor\b[^.;]*\bonly\b")


def classify(statement: str) -> str | None:
    text = " ".join(statement.lower().split())
    if text.startswith("retired:") or _RESTRICTION.search(text) or _SCOPED.search(text):
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
    skipped: list[str] = []
    for record in project.list("score:constraint"):
        if record["lifecycle_state"] != "active":
            continue
        level = classify(_text(record, "statement"))
        if level is None:
            continue
        effort = resolve_effort(record, known)
        if effort:
            mappings.append(Mapping(record["id"], record["subject"], effort, level))
        else:
            skipped.append(record["subject"])
    return sorted(mappings, key=lambda m: (m.effort, m.constraint)), sorted(skipped)


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
