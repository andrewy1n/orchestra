from __future__ import annotations

from collections.abc import Sequence

from orchestra.canon.types import Record
from orchestra.composer.architecture import (
    Component,
    Interface,
    Scope,
    UnknownScopeError,
    query_architecture,
)
from orchestra.composer.records import current_product, current_product_items
from orchestra.score.planning.standing_constraint import read_standing_constraint


def _product_context(records: Sequence[Record], area: str) -> str:
    lines = [f"## Product context for {area}"]
    product = current_product(records)
    if product is not None:
        lines.extend((product.purpose, f"Audience: {product.audience}"))
    capabilities = [
        f"- **{item.title}**: {item.description}"
        for item in current_product_items(records)
        if item.status == "current" and item.area == area
    ]
    lines.extend(capabilities or ["No current capabilities are assigned to this area."])
    return "\n\n".join(lines)


def _decisions(node: Component | Interface) -> list[str]:
    return [
        f"- Accepted ADR **{decision.title}**: {decision.rationale}"
        for decision in node.decisions
        if decision.status == "accepted"
    ]


def _architecture_context(records: Sequence[Record], scope: Scope) -> str:
    try:
        model = query_architecture(records, scope)
    except UnknownScopeError:
        if scope.kind == "area":
            return f"No architecture components for area `{scope.name}`."
        raise
    components = [component for items in model.areas.values() for component in items]
    interfaces = model.interfaces
    if components:
        names = {component.name for component in components}
        interfaces = tuple(
            interface
            for interface in query_architecture(records).interfaces
            if names.intersection(interface.connects)
        )
    lines = [f"## Architecture context for {scope.kind} {scope.name}"]
    for component in components:
        lines.extend((f"### {component.name}", component.responsibility, *_decisions(component)))
    for interface in interfaces:
        lines.extend((f"### {interface.name}", interface.provides, *_decisions(interface)))
    constraints = {name for node in (*components, *interfaces) for name in node.constraints}
    for name in sorted(constraints):
        constraint = read_standing_constraint(model.constraints[name])
        lines.append(
            f"- **{constraint.name}** (version `{constraint.id}`): {constraint.rule} "
            f"Basis: {constraint.basis}"
        )
    return "\n\n".join(lines)


def project_context(records: Sequence[Record], kind: str, name: str) -> str:
    if kind == "product":
        return _product_context(records, name)
    return _architecture_context(records, Scope(kind, name))
