from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TypeAlias

from orchestra.canon.index import RecordIndex
from orchestra.canon.types import Record

_RANGE = re.compile(r"^(\d+)-(\d+)$")


class PhaseSelectionError(ValueError):
    pass


@dataclass(frozen=True)
class PhaseSelection:
    effort: Record
    phase_subjects: tuple[str, ...]
    dependency_order: tuple[str, ...]
    external_dependencies: tuple[str, ...]


PhaseMap: TypeAlias = dict[str, Record]


def _ordinal(record: Record) -> int:
    value = record["payload"].get("ordinal")
    if not isinstance(value, int) or isinstance(value, bool):
        raise PhaseSelectionError(f"phase {record['subject']!r} has no valid ordinal")
    return value


def _dependency_values(record: Record) -> list[str]:
    value = record["payload"].get("depends_on", [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PhaseSelectionError(f"phase {record['subject']!r} has invalid dependencies")
    return [item for item in value if isinstance(item, str)]


def _effort_phases(records: list[Record], effort_subject: str) -> tuple[Record, PhaseMap, PhaseMap]:
    index = RecordIndex(records)
    effort = index.resolve_subject("score:effort", effort_subject)
    if effort is None:
        raise PhaseSelectionError(f"unknown effort {effort_subject!r}")
    all_phases = {
        record["subject"]: record
        for record in records
        if record["record_type"] == "score:phase" and record["lifecycle_state"] != "superseded"
    }
    phases = {
        subject: record
        for subject, record in all_phases.items()
        if record["payload"].get("effort") == effort_subject
    }
    return effort, phases, all_phases


def _select_tokens(scoped: PhaseMap, all_phases: PhaseMap, selector: str) -> list[str]:
    ordinals: dict[int, list[str]] = {}
    for subject, phase in scoped.items():
        ordinals.setdefault(_ordinal(phase), []).append(subject)
    for subjects in ordinals.values():
        subjects.sort()
    selected: list[str] = []
    tokens = selector.split(",")
    if not selector or any(not token.strip() for token in tokens):
        raise PhaseSelectionError("phase selection must not be empty")
    for raw in tokens:
        token = raw.strip()
        if token in scoped:
            matches = [token]
        elif token.isdigit():
            matches = ordinals.get(int(token), [])
            if not matches:
                raise PhaseSelectionError(f"unknown phase ordinal {token!r}")
            if len(matches) > 1:
                raise PhaseSelectionError(f"ambiguous phase ordinal {token!r}")
        elif match := _RANGE.fullmatch(token):
            start, end = (int(part) for part in match.groups())
            if start > end:
                raise PhaseSelectionError(f"invalid phase range {token!r}")
            missing = [number for number in range(start, end + 1) if number not in ordinals]
            if missing:
                raise PhaseSelectionError(f"phase range {token!r} has missing members {missing}")
            ambiguous = [number for number in range(start, end + 1) if len(ordinals[number]) > 1]
            if ambiguous:
                raise PhaseSelectionError(
                    f"phase range {token!r} has ambiguous members {ambiguous}"
                )
            matches = [ordinals[number][0] for number in range(start, end + 1)]
        elif token in all_phases:
            raise PhaseSelectionError(f"phase {token!r} belongs to another effort")
        else:
            raise PhaseSelectionError(f"unknown phase selector {token!r}")
        for subject in matches:
            if subject not in selected:
                selected.append(subject)
    return selected


def resolve_phase_selection(
    records: list[Record], effort_subject: str, selector: str
) -> PhaseSelection:
    effort, scoped, all_phases = _effort_phases(records, effort_subject)
    selected = _select_tokens(scoped, all_phases, selector)
    selected_set = set(selected)
    dependencies: dict[str, list[str]] = {}
    external: set[str] = set()
    for subject in selected:
        phase_dependencies: list[str] = []
        for dependency in _dependency_values(scoped[subject]):
            if dependency == subject:
                raise PhaseSelectionError(f"phase {subject!r} depends on itself")
            target = all_phases.get(dependency)
            if target is None:
                raise PhaseSelectionError(
                    f"phase {subject!r} depends on unknown phase {dependency!r}"
                )
            if target["payload"].get("effort") != effort_subject:
                raise PhaseSelectionError(
                    f"phase {subject!r} depends on phase {dependency!r} from another effort"
                )
            if dependency in selected_set:
                phase_dependencies.append(dependency)
            else:
                external.add(dependency)
        dependencies[subject] = phase_dependencies

    remaining = {subject: set(items) for subject, items in dependencies.items()}
    ordered: list[str] = []
    while remaining:
        ready = [subject for subject, items in remaining.items() if not items]
        if not ready:
            raise PhaseSelectionError("phase dependencies contain a cycle")
        ready.sort(key=lambda subject: (_ordinal(scoped[subject]), subject))
        for subject in ready:
            ordered.append(subject)
            remaining.pop(subject)
        for items in remaining.values():
            items.difference_update(ready)

    external_dependencies = tuple(
        sorted(external, key=lambda subject: (_ordinal(all_phases[subject]), subject))
    )
    return PhaseSelection(
        effort=effort,
        phase_subjects=tuple(selected),
        dependency_order=tuple(ordered),
        external_dependencies=external_dependencies,
    )
