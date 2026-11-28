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
from orchestra.composer.records import current_area, current_product, current_product_items
from orchestra.score.planning.standing_constraint import (
    StandingConstraint,
    applicable,
    declared_areas,
    read_standing_constraint,
)


def _known_area(records: Sequence[Record], name: str) -> bool:
    return current_area(records, name) is not None or name in declared_areas(records)


def _constraint_section(constraints: Sequence[StandingConstraint]) -> str:
    unique = {constraint.id: constraint for constraint in constraints}
    return "\n\n".join(
        [
            "## Applicable standing constraints",
            *(
                f"### {constraint.name}\n"
                f"**area**: {constraint.area}; **version**: {constraint.id}\n\n"
                f"**rule**: {constraint.rule}\n\n"
                f"**basis**: {constraint.basis}"
                for constraint in sorted(unique.values(), key=lambda rule: (rule.name, rule.id))
            ),
        ]
    )


def _product_context(records: Sequence[Record], area: str) -> str:
    if not _known_area(records, area):
        raise UnknownScopeError(area, "scope", "names no area")
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


def _architecture_context(
    records: Sequence[Record], scope: Scope
) -> tuple[str, list[StandingConstraint]]:
    try:
        model = query_architecture(records, scope)
    except UnknownScopeError:
        if scope.kind != "area" or not _known_area(records, scope.name):
            raise
        return (
            f"No architecture components for area `{scope.name}`.",
            applicable(records, scope.name),
        )
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
    names = {name for node in (*components, *interfaces) for name in node.constraints}
    constraints = [read_standing_constraint(model.constraints[name]) for name in names]
    if scope.kind == "area":
        constraints.extend(applicable(records, scope.name))
    return "\n\n".join(lines), constraints


def project_context(records: Sequence[Record], kind: str, names: Sequence[str]) -> str:
    if kind == "product":
        return "\n\n".join(_product_context(records, name) for name in dict.fromkeys(names))

    sections: list[str] = []
    constraints: list[StandingConstraint] = []
    for name in dict.fromkeys(names):
        section, applicable_rules = _architecture_context(records, Scope(kind, name))
        sections.append(section)
        constraints.extend(applicable_rules)
        if not applicable_rules and kind == "area":
            sections.append(f"No standing constraints for area `{name}`.")
    if constraints:
        sections.append(_constraint_section(constraints))
    return "\n\n".join(sections)
