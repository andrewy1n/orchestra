from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.fields import optional_text_list
from orchestra.canon.types import Record
from orchestra.composer.records import (
    ARCHITECTURE_DECISION,
    COMPONENT,
    INTERFACE,
    ArchitectureDecision,
    read_architecture_decision,
    read_component,
    read_interface,
)
from orchestra.composer.records import Component as ComponentRecord
from orchestra.composer.records import Interface as InterfaceRecord
from orchestra.score.lookups import latest_record

STANDING_CONSTRAINT = "score:standing-constraint"
_DEAD_STATES = ("superseded", "retracted")


@dataclass(frozen=True)
class Decision:
    title: str
    rationale: str
    status: str
    enforced_by: tuple[str, ...]


@dataclass(frozen=True)
class Component:
    name: str
    area: str
    responsibility: str
    decisions: tuple[Decision, ...]
    constraints: tuple[str, ...]


@dataclass(frozen=True)
class Interface:
    name: str
    provides: str
    connects: tuple[str, ...]
    decisions: tuple[Decision, ...]
    constraints: tuple[str, ...]


@dataclass(frozen=True)
class Architecture:
    areas: dict[str, tuple[Component, ...]]
    interfaces: tuple[Interface, ...]


def _current(records: Sequence[Record], record_type: str) -> list[Record]:
    by_subject: dict[str, list[Record]] = {}
    for record in records:
        if record["record_type"] == record_type and record["lifecycle_state"] not in _DEAD_STATES:
            by_subject.setdefault(record["subject"], []).append(record)
    latest = (latest_record(group) for group in by_subject.values())
    return sorted((r for r in latest if r is not None), key=lambda r: r["subject"])


def _require(record: Record, field: str, names: Iterable[str], known: set[str], kind: str) -> None:
    for name in names:
        if name not in known:
            raise RecordShapeError(record["id"], field, f"names missing {kind} {name}")


def _decision(source: ArchitectureDecision) -> Decision:
    return Decision(source.title, source.rationale, source.status, source.enforced_by)


def _constraints_for(
    name: str,
    decisions: Sequence[ArchitectureDecision],
    targets: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    names = {constraint for constraint, hit in targets.items() if name in hit}
    for decision in decisions:
        names.update(decision.enforced_by)
    return tuple(sorted(names))


def _build(records: Sequence[Record]) -> Architecture:
    components = [read_component(r) for r in _current(records, COMPONENT)]
    interfaces = [read_interface(r) for r in _current(records, INTERFACE)]
    decisions = [read_architecture_decision(r) for r in _current(records, ARCHITECTURE_DECISION)]
    constraint_records = _current(records, STANDING_CONSTRAINT)

    component_names = {c.name for c in components}
    subject_names = component_names | {i.name for i in interfaces}
    constraint_names = {r["subject"] for r in constraint_records}

    for interface in interfaces:
        _require(interface.record, "connects", interface.connects, component_names, "component")
    for decision in decisions:
        _require(
            decision.record, "affects", decision.affects, subject_names, "component or interface"
        )
        _require(
            decision.record, "enforced_by", decision.enforced_by, constraint_names, "constraint"
        )
    targets: dict[str, tuple[str, ...]] = {}
    for record in constraint_records:
        hit = optional_text_list(record, record_payload(record), "targets")
        _require(record, "targets", hit, subject_names, "component or interface")
        targets[record["subject"]] = hit

    def affecting(name: str) -> list[ArchitectureDecision]:
        return [d for d in decisions if name in d.affects]

    def component_view(source: ComponentRecord) -> Component:
        hits = affecting(source.name)
        return Component(
            source.name,
            source.area,
            source.responsibility,
            tuple(_decision(d) for d in hits),
            _constraints_for(source.name, hits, targets),
        )

    def interface_view(source: InterfaceRecord) -> Interface:
        hits = affecting(source.name)
        return Interface(
            source.name,
            source.provides,
            source.connects,
            tuple(_decision(d) for d in hits),
            _constraints_for(source.name, hits, targets),
        )

    areas: dict[str, list[Component]] = {}
    for component in components:
        areas.setdefault(component.area, []).append(component_view(component))
    return Architecture(
        areas={area: tuple(items) for area, items in sorted(areas.items())},
        interfaces=tuple(interface_view(i) for i in interfaces),
    )


def current_architecture(records: Sequence[Record]) -> Architecture:
    return _build(records)


def query_architecture(records: Sequence[Record], scope: str | None = None) -> Architecture:
    model = _build(records)
    if scope is None:
        return model
    for items in model.areas.values():
        for component in items:
            if component.name == scope:
                return Architecture({component.area: (component,)}, ())
    for interface in model.interfaces:
        if interface.name == scope:
            return Architecture({}, (interface,))
    if scope in model.areas:
        return Architecture({scope: model.areas[scope]}, ())
    raise RecordShapeError(scope, "scope", "names no area, component or interface")
