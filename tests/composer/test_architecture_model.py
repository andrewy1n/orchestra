from __future__ import annotations

import pytest

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.composer.architecture import (
    Architecture,
    Component,
    Interface,
    current_architecture,
    query_architecture,
)
from orchestra.composer.records import ARCHITECTURE_DECISION, COMPONENT, INTERFACE

CONSTRAINT = "score:standing-constraint"


def _names(values: list[str]) -> list[JsonValue]:
    return list(values)


def _record(
    record_type: str,
    subject: str,
    payload: JsonObject,
    body: str,
    record_id: str,
    state: str = "active",
    recorded_at: str = "2026-01-01T00:00:00Z",
) -> Record:
    return {
        "id": record_id,
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "body": body,
        "lifecycle_state": state,
        "relationships": {},
        "revision": "r",
        "recorded_at": recorded_at,
    }


def _component(name: str, area: str = "composer", record_id: str = "") -> Record:
    return _record(
        COMPONENT,
        name,
        {"area": area},
        f"## Responsibility\nOwns {name}.",
        record_id or f"component-{name}",
    )


def _interface(name: str, connects: list[str], record_id: str = "") -> Record:
    return _record(
        INTERFACE,
        name,
        {"connects": _names(connects)},
        f"## Provides\nServes {name}.",
        record_id or f"interface-{name}",
    )


def _decision(
    title: str,
    affects: list[str],
    status: str = "accepted",
    enforced_by: list[str] | None = None,
    record_id: str = "",
    state: str = "active",
    recorded_at: str = "2026-01-01T00:00:00Z",
    rationale: str = "Because.",
) -> Record:
    payload: JsonObject = {"status": status, "affects": _names(affects)}
    if enforced_by is not None:
        payload["enforced_by"] = _names(enforced_by)
    return _record(
        ARCHITECTURE_DECISION,
        title,
        payload,
        f"## Rationale\n{rationale}",
        record_id or f"decision-{title}-{recorded_at}",
        state,
        recorded_at,
    )


def _constraint(
    name: str, targets: list[str] | None = None, state: str = "active", record_id: str = ""
) -> Record:
    payload: JsonObject = {"area": "composer", "rule": "Do it.", "check": "true"}
    if targets is not None:
        payload["targets"] = _names(targets)
    return _record(
        CONSTRAINT, name, payload, "## Basis\nWhy.", record_id or f"constraint-{name}", state
    )


def _component_of(model: Architecture, name: str) -> Component:
    for components in model.areas.values():
        for component in components:
            if component.name == name:
                return component
    raise AssertionError(f"component {name} not in model")


def _interface_of(model: Architecture, name: str) -> Interface:
    for interface in model.interfaces:
        if interface.name == name:
            return interface
    raise AssertionError(f"interface {name} not in model")


def _titles(component: Component | Interface) -> list[str]:
    return [decision.title for decision in component.decisions]


def test_supersede_replacement_decision_shows_only_current_record() -> None:
    records = [
        _component("records"),
        _decision("Typed", ["records"], rationale="Old.", recorded_at="2026-01-01T00:00:00Z"),
        _decision("Typed", ["records"], rationale="New.", recorded_at="2026-02-01T00:00:00Z"),
    ]
    decisions = _component_of(current_architecture(records), "records").decisions
    assert [d.rationale for d in decisions] == ["New."]


def test_supersede_state_record_never_appears_in_current_view() -> None:
    records = [
        _component("records"),
        _decision("Old way", ["records"], state="superseded"),
        _decision("New way", ["records"]),
    ]
    model = current_architecture(records)
    assert _titles(_component_of(model, "records")) == ["New way"]


def test_supersede_record_stays_in_input_history() -> None:
    old = _decision("Typed", ["records"], state="superseded", record_id="old")
    records = [_component("records"), old, _decision("Typed", ["records"], record_id="new")]
    current_architecture(records)
    assert old in records
    assert old["lifecycle_state"] == "superseded"


def test_supersede_replaced_decision_does_not_resolve_dropped_names() -> None:
    records = [
        _component("records"),
        _decision("Typed", ["gone"], state="superseded"),
        _decision("Typed", ["records"]),
    ]
    assert _titles(_component_of(current_architecture(records), "records")) == ["Typed"]


def test_supersede_component_keeps_only_latest_record() -> None:
    records = [
        _record(
            COMPONENT,
            "records",
            {"area": "old"},
            "## Responsibility\nOld.",
            "c1",
            recorded_at="2026-01-01T00:00:00Z",
        ),
        _record(
            COMPONENT,
            "records",
            {"area": "new"},
            "## Responsibility\nNew.",
            "c2",
            recorded_at="2026-02-01T00:00:00Z",
        ),
    ]
    model = current_architecture(records)
    assert list(model.areas) == ["new"]
    assert _component_of(model, "records").responsibility == "New."


def test_enforced_by_decision_lists_constraint_names_on_component() -> None:
    records = [
        _component("records"),
        _constraint("typed-reads"),
        _decision("Typed", ["records"], enforced_by=["typed-reads"]),
    ]
    model = current_architecture(records)
    component = _component_of(model, "records")
    assert component.decisions[0].enforced_by == ("typed-reads",)
    assert "typed-reads" in component.constraints


def test_enforced_by_constraint_stays_on_constraint_record() -> None:
    records = [
        _component("records"),
        _constraint("typed-reads"),
        _decision("Typed", ["records"], enforced_by=["typed-reads"]),
    ]
    decision = _component_of(current_architecture(records), "records").decisions[0]
    assert not hasattr(decision, "rule")
    assert not hasattr(decision, "check")


def test_enforced_by_unknown_constraint_raises_naming_decision_id() -> None:
    records = [
        _component("records"),
        _decision("Typed", ["records"], enforced_by=["nope"], record_id="dec-1"),
    ]
    with pytest.raises(RecordShapeError) as error:
        current_architecture(records)
    assert error.value.record_id == "dec-1"


def test_enforced_by_retracted_constraint_raises() -> None:
    records = [
        _component("records"),
        _constraint("typed-reads", state="retracted"),
        _decision("Typed", ["records"], enforced_by=["typed-reads"], record_id="dec-1"),
    ]
    with pytest.raises(RecordShapeError):
        current_architecture(records)


def test_enforced_by_target_constraint_shows_by_name_on_interface() -> None:
    records = [
        _component("records"),
        _interface("read-api", ["records"]),
        _constraint("api-stable", targets=["read-api"]),
    ]
    model = current_architecture(records)
    assert _interface_of(model, "read-api").constraints == ("api-stable",)
    assert _component_of(model, "records").constraints == ()


def test_enforced_by_constraint_without_targets_is_not_attached() -> None:
    records = [_component("records"), _constraint("general")]
    assert _component_of(current_architecture(records), "records").constraints == ()


def test_missing_affected_name_raises_naming_decision_id() -> None:
    records = [_component("records"), _decision("Typed", ["ghost"], record_id="dec-1")]
    with pytest.raises(RecordShapeError) as error:
        current_architecture(records)
    assert error.value.record_id == "dec-1"


def test_missing_connected_component_raises_naming_interface_id() -> None:
    records = [_component("records"), _interface("read-api", ["records", "ghost"], "if-1")]
    with pytest.raises(RecordShapeError) as error:
        current_architecture(records)
    assert error.value.record_id == "if-1"


def test_missing_constraint_target_raises_naming_constraint_id() -> None:
    records = [_component("records"), _constraint("c", targets=["ghost"], record_id="con-1")]
    with pytest.raises(RecordShapeError) as error:
        current_architecture(records)
    assert error.value.record_id == "con-1"


def test_missing_target_when_superseded_target_only_raises() -> None:
    records = [
        _component("records", record_id="c1"),
        _record(COMPONENT, "old", {"area": "x"}, "## Responsibility\nR.", "c2", state="superseded"),
        _decision("Typed", ["old"], record_id="dec-1"),
    ]
    with pytest.raises(RecordShapeError) as error:
        current_architecture(records)
    assert error.value.record_id == "dec-1"


def test_missing_error_also_raised_by_scoped_query() -> None:
    records = [_component("records"), _decision("Typed", ["ghost"], record_id="dec-1")]
    with pytest.raises(RecordShapeError):
        query_architecture(records, "records")


def test_missing_decision_names_nothing_raises() -> None:
    bad = _decision("Typed", ["records"], record_id="dec-1")
    bad["payload"] = {"status": "accepted", "affects": []}
    with pytest.raises(RecordShapeError) as error:
        current_architecture([_component("records"), bad])
    assert error.value.record_id == "dec-1"


def test_missing_name_is_not_dropped_from_view_silently() -> None:
    records = [_component("records"), _decision("Typed", ["ghost"], record_id="dec-1")]
    with pytest.raises(RecordShapeError):
        current_architecture(records)


def test_model_groups_components_by_area() -> None:
    records = [_component("a", "one"), _component("b", "two"), _component("c", "one")]
    model = current_architecture(records)
    assert {area: [c.name for c in cs] for area, cs in model.areas.items()} == {
        "one": ["a", "c"],
        "two": ["b"],
    }


def test_model_carries_accepted_with_rationale_and_proposed_marked() -> None:
    records = [
        _component("records"),
        _decision("Done", ["records"], rationale="Reason."),
        _decision("Maybe", ["records"], status="proposed"),
    ]
    decisions = {
        d.title: d for d in _component_of(current_architecture(records), "records").decisions
    }
    assert decisions["Done"].status == "accepted"
    assert decisions["Done"].rationale == "Reason."
    assert decisions["Maybe"].status == "proposed"


def test_scope_by_area_returns_only_that_area() -> None:
    records = [_component("a", "one"), _component("b", "two")]
    model = query_architecture(records, "one")
    assert isinstance(model, Architecture)
    assert list(model.areas) == ["one"]


def test_scope_by_component_returns_that_component_and_its_decisions() -> None:
    records = [
        _component("a"),
        _component("b"),
        _decision("DA", ["a"]),
        _decision("DB", ["b"]),
    ]
    model = query_architecture(records, "a")
    assert _titles(_component_of(model, "a")) == ["DA"]
    with pytest.raises(AssertionError):
        _component_of(model, "b")


def test_scope_by_interface_returns_connected_component_names() -> None:
    records = [
        _component("a"),
        _component("b"),
        _component("c"),
        _interface("api", ["a", "b"]),
        _decision("DI", ["api"]),
        _constraint("k", targets=["api"]),
    ]
    model = query_architecture(records, "api")
    interface = _interface_of(model, "api")
    assert interface.connects == ("a", "b")
    assert _titles(interface) == ["DI"]
    assert interface.constraints == ("k",)


def test_scope_decision_shows_under_every_scope_it_names() -> None:
    records = [
        _component("a"),
        _component("b", "other"),
        _interface("api", ["a"]),
        _decision("Shared", ["a", "b", "api"]),
    ]
    assert _titles(_component_of(query_architecture(records, "a"), "a")) == ["Shared"]
    assert _titles(_component_of(query_architecture(records, "b"), "b")) == ["Shared"]
    assert _titles(_interface_of(query_architecture(records, "api"), "api")) == ["Shared"]


def test_scope_none_returns_whole_model_with_components_and_interfaces() -> None:
    records = [_component("a"), _interface("api", ["a"]), _decision("D", ["a"])]
    model = query_architecture(records, None)
    assert model == current_architecture(records)
    assert _titles(_component_of(model, "a")) == ["D"]
    assert _interface_of(model, "api").connects == ("a",)


def test_enforced_by_union_of_targets_and_decision_constraints_on_component() -> None:
    records = [
        _component("records"),
        _constraint("by-target", targets=["records"]),
        _constraint("by-decision"),
        _decision("Typed", ["records"], enforced_by=["by-decision"]),
    ]
    component = _component_of(current_architecture(records), "records")
    assert component.constraints == ("by-decision", "by-target")


def test_enforced_by_union_of_targets_and_decision_constraints_on_interface() -> None:
    records = [
        _component("records"),
        _interface("api", ["records"]),
        _constraint("by-target", targets=["api"]),
        _constraint("by-decision"),
        _decision("Typed", ["api"], enforced_by=["by-decision"]),
    ]
    interface = _interface_of(current_architecture(records), "api")
    assert interface.constraints == ("by-decision", "by-target")


def test_scope_unknown_name_raises() -> None:
    with pytest.raises(RecordShapeError):
        query_architecture([_component("a")], "ghost")
