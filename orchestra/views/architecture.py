from __future__ import annotations

from collections.abc import Sequence

from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.composer.architecture import (
    Component,
    Decision,
    Interface,
    Scope,
    query_architecture,
)
from orchestra.conductor.verification.standing_constraints import constraint_outcomes
from orchestra.score.planning.standing_constraint import read_standing_constraint

NO_COMPONENT = "No component exists."


def _decision(decision: Decision) -> JsonObject:
    return {
        "title": decision.title,
        "rationale": decision.rationale,
        "status": decision.status,
    }


def _constraints(
    names: Sequence[str], by_name: dict[str, Record], records: Sequence[Record], revision: str
) -> list[JsonValue]:
    selected = [by_name[name] for name in names]
    results = constraint_outcomes(records, [r["id"] for r in selected], revision)
    items: list[JsonValue] = []
    for record, result in zip(selected, results, strict=True):
        declared = read_standing_constraint(record)
        items.append(
            {
                "name": declared.name,
                "rule": declared.rule,
                "check": declared.check,
                "outcome": result.outcome,
                "constraint_id": result.constraint_id,
                "revision": result.revision,
            }
        )
    return items


def _component(
    component: Component,
    connecting: Sequence[str],
    by_name: dict[str, Record],
    records: Sequence[Record],
    revision: str,
) -> JsonObject:
    return {
        "name": component.name,
        "responsibility": component.responsibility,
        "interfaces": list(connecting),
        "decisions": [_decision(d) for d in component.decisions],
        "constraints": _constraints(component.constraints, by_name, records, revision),
    }


def _interface(
    interface: Interface,
    by_name: dict[str, Record],
    records: Sequence[Record],
    revision: str,
) -> JsonObject:
    return {
        "name": interface.name,
        "provides": interface.provides,
        "connects": list(interface.connects),
        "decisions": [_decision(d) for d in interface.decisions],
        "constraints": _constraints(interface.constraints, by_name, records, revision),
    }


def architecture_view(
    records: Sequence[Record], scope: Scope | None = None, revision: str = ""
) -> JsonObject:
    model = query_architecture(records, scope)
    connected = model if scope is None else query_architecture(records)
    by_name = model.constraints
    connecting: dict[str, list[str]] = {}
    for interface in connected.interfaces:
        for name in interface.connects:
            connecting.setdefault(name, []).append(interface.name)
    areas: list[JsonValue] = [
        {
            "name": area,
            "components": [
                _component(c, connecting.get(c.name, []), by_name, records, revision)
                for c in components
            ],
        }
        for area, components in model.areas.items()
    ]
    interfaces: list[JsonValue] = [
        _interface(i, by_name, records, revision) for i in model.interfaces
    ]
    return {"revision": revision, "areas": areas, "interfaces": interfaces}


def _items(value: JsonValue) -> list[JsonObject]:
    if not isinstance(value, list):
        raise TypeError("architecture view field is not a list")
    items: list[JsonObject] = []
    for item in value:
        if not isinstance(item, dict):
            raise TypeError("architecture view item is not an object")
        items.append(item)
    return items


def _decision_lines(node: JsonObject) -> list[str]:
    lines: list[str] = []
    for decision in _items(node["decisions"]):
        mark = " (proposed)" if decision["status"] == "proposed" else ""
        lines.append(f"- decision **{decision['title']}**{mark}: {decision['rationale']}")
    return lines


def _constraint_lines(node: JsonObject) -> list[str]:
    return [
        f"- constraint **{c['name']}**: {c['rule']}; check: {c['check']}; "
        f"outcome: {c['outcome']}; constraint id: {c['constraint_id']}; revision: {c['revision']}"
        for c in _items(node["constraints"])
    ]


def render_architecture(view: JsonObject) -> str:
    areas = _items(view["areas"])
    interfaces = _items(view["interfaces"])
    if not areas and not interfaces:
        return NO_COMPONENT
    lines = ["# Architecture", ""]
    for area in areas:
        lines += [f"## {area['name']}", ""]
        for component in _items(area["components"]):
            lines += [f"### {component['name']}", "", str(component["responsibility"]), ""]
            connecting = component["interfaces"]
            if isinstance(connecting, list) and connecting:
                lines.append("- interfaces: " + ", ".join(str(n) for n in connecting))
            lines += _decision_lines(component) + _constraint_lines(component) + [""]
    if interfaces:
        lines += ["## Interfaces", ""]
    for interface in interfaces:
        connects = interface["connects"]
        names = ", ".join(str(n) for n in connects) if isinstance(connects, list) else ""
        lines += [f"### {interface['name']}", "", str(interface["provides"]), ""]
        lines.append(f"- connects: {names}")
        lines += _decision_lines(interface) + _constraint_lines(interface) + [""]
    return "\n".join(lines).rstrip("\n")
