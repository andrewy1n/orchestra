from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeAlias

from orchestra.canon import record_payload
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.index import RecordIndex
from orchestra.canon.types import Record
from orchestra.score.lookups import current_phases
from orchestra.score.phase import Phase, read_phase

_RANGE = re.compile(r"^(\d+)-(\d+)$")


class PhaseSelectionError(ValueError):
    pass


@dataclass(frozen=True)
class PhaseSelection:
    effort: Record
    phase_subjects: tuple[str, ...]
    dependency_order: tuple[str, ...]
    external_dependencies: tuple[str, ...]


PhaseMap: TypeAlias = dict[str, Phase]


def _dependency_values(phase: Phase) -> list[str]:
    value = phase.record["payload"].get("depends_on", [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PhaseSelectionError(f"phase {phase.subject!r} has invalid dependencies")
    return [item for item in value if isinstance(item, str)]


def _read_scoped(slug: str, record: Record) -> Phase:
    try:
        return read_phase(record)
    except RecordShapeError as exc:
        raise PhaseSelectionError(f"phase {slug!r}: {exc}") from exc


def _effort_phases(
    records: list[Record], effort_subject: str
) -> tuple[Record, PhaseMap, Mapping[str, object]]:
    index = RecordIndex(records)
    effort = index.resolve_subject("score:effort", effort_subject)
    if effort is None:
        raise PhaseSelectionError(f"unknown effort {effort_subject!r}")
    current = current_phases(records)
    efforts = {slug: record_payload(record).get("effort") for slug, record in current.items()}
    phases = {
        slug: _read_scoped(slug, record)
        for slug, record in current.items()
        if efforts[slug] == effort_subject
    }
    return effort, phases, efforts


def _select_tokens(scoped: PhaseMap, all_efforts: Mapping[str, object], selector: str) -> list[str]:
    ordinals: dict[int, list[str]] = {}
    for subject, phase in scoped.items():
        ordinals.setdefault(phase.ordinal, []).append(subject)
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
        elif token in all_efforts:
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
    effort, scoped, all_efforts = _effort_phases(records, effort_subject)
    selected = _select_tokens(scoped, all_efforts, selector)
    selected_set = set(selected)
    dependencies: dict[str, list[str]] = {}
    external: set[str] = set()
    for subject in selected:
        phase_dependencies: list[str] = []
        for dependency in _dependency_values(scoped[subject]):
            if dependency == subject:
                raise PhaseSelectionError(f"phase {subject!r} depends on itself")
            if dependency not in all_efforts:
                raise PhaseSelectionError(
                    f"phase {subject!r} depends on unknown phase {dependency!r}"
                )
            if all_efforts[dependency] != effort_subject:
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
        ready.sort(key=lambda subject: (scoped[subject].ordinal, subject))
        for subject in ready:
            ordered.append(subject)
            remaining.pop(subject)
        for items in remaining.values():
            items.difference_update(ready)

    external_dependencies = tuple(
        sorted(external, key=lambda subject: (scoped[subject].ordinal, subject))
    )
    return PhaseSelection(
        effort=effort,
        phase_subjects=tuple(selected),
        dependency_order=tuple(ordered),
        external_dependencies=external_dependencies,
    )
