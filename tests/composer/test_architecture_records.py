from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import JsonObject, Record
from orchestra.composer.records import (
    ARCHITECTURE_DECISION,
    COMPONENT,
    INTERFACE,
    read_architecture_decision,
    read_component,
    read_interface,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSER_SCHEMA = REPO_ROOT / "orchestra" / "composer" / "schemas" / "composer.json"
SCORE_SCHEMA = REPO_ROOT / "orchestra" / "score" / "schemas" / "score.json"


def _record(record_type: str, subject: str, payload: JsonObject, body: str = "") -> Record:
    return {
        "id": "r1",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "body": body,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r",
        "recorded_at": "2026-01-01T00:00:00Z",
    }


def _component(payload: JsonObject | None = None) -> Record:
    payload = {"area": "composer"} if payload is None else payload
    return _record(COMPONENT, "records", payload, "## Responsibility\nStore records.")


def _interface(payload: JsonObject | None = None) -> Record:
    payload = {"connects": ["records", "views"]} if payload is None else payload
    return _record(INTERFACE, "read-api", payload, "## Provides\nTyped reads.")


def _decision(payload: JsonObject | None = None) -> Record:
    payload = (
        {"status": "accepted", "affects": ["records"], "enforced_by": ["c1"]}
        if payload is None
        else payload
    )
    return _record(
        ARCHITECTURE_DECISION, "Keep records typed", payload, "## Rationale\nShape errors early."
    )


def test_component_reads_name_area_and_responsibility() -> None:
    component = read_component(_component())
    assert component.name == "records"
    assert component.area == "composer"
    assert component.responsibility == "Store records."


def test_component_without_area_raises_shape_error() -> None:
    with pytest.raises(RecordShapeError):
        read_component(_component({}))


def test_component_without_responsibility_raises_shape_error() -> None:
    record = _component()
    record["body"] = ""
    with pytest.raises(RecordShapeError):
        read_component(record)


def test_component_type_is_in_composer_schema() -> None:
    types = json.loads(COMPOSER_SCHEMA.read_text())["types"]
    assert "component" in types
    assert types["component"]["fields"]["area"] == {"type": "string"}
    assert types["component"]["sections"] == ["Responsibility"]


def test_interface_reads_name_provides_and_connects() -> None:
    interface = read_interface(_interface())
    assert interface.name == "read-api"
    assert interface.provides == "Typed reads."
    assert interface.connects == ("records", "views")


def test_interface_without_connects_raises_shape_error() -> None:
    with pytest.raises(RecordShapeError):
        read_interface(_interface({}))


def test_interface_with_non_list_connects_raises_shape_error() -> None:
    with pytest.raises(RecordShapeError):
        read_interface(_interface({"connects": "records"}))


def test_interface_without_provides_raises_shape_error() -> None:
    record = _interface()
    record["body"] = ""
    with pytest.raises(RecordShapeError):
        read_interface(record)


def test_interface_type_is_in_composer_schema() -> None:
    types = json.loads(COMPOSER_SCHEMA.read_text())["types"]
    assert "interface" in types
    assert types["interface"]["sections"] == ["Provides"]


def test_decision_fields_read_title_rationale_affects_and_enforced_by() -> None:
    decision = read_architecture_decision(_decision())
    assert decision.title == "Keep records typed"
    assert decision.rationale == "Shape errors early."
    assert decision.status == "accepted"
    assert decision.affects == ("records",)
    assert decision.enforced_by == ("c1",)


def test_decision_fields_enforced_by_defaults_to_empty() -> None:
    decision = read_architecture_decision(_decision({"status": "proposed", "affects": ["a"]}))
    assert decision.enforced_by == ()
    assert decision.status == "proposed"


def test_decision_fields_without_affects_raises_shape_error() -> None:
    with pytest.raises(RecordShapeError):
        read_architecture_decision(_decision({"status": "accepted"}))


def test_decision_fields_with_empty_affects_raises_shape_error() -> None:
    with pytest.raises(RecordShapeError):
        read_architecture_decision(_decision({"status": "accepted", "affects": []}))


def test_decision_fields_without_rationale_raises_shape_error() -> None:
    record = _decision()
    record["body"] = ""
    with pytest.raises(RecordShapeError):
        read_architecture_decision(record)


def test_decision_fields_type_is_in_composer_schema() -> None:
    types = json.loads(COMPOSER_SCHEMA.read_text())["types"]
    fields = types["architecture-decision"]["fields"]
    assert set(fields) == {"status", "affects", "enforced_by"}
    assert fields["affects"] == {"list": {"type": "string"}}
    assert fields["enforced_by"] == {"list": {"type": "string"}, "optional": True}
    assert types["architecture-decision"]["sections"] == ["Rationale"]


def test_decision_status_missing_raises_shape_error() -> None:
    with pytest.raises(RecordShapeError):
        read_architecture_decision(_decision({"affects": ["records"]}))


@pytest.mark.parametrize("value", ["rejected", "", "Accepted", 1])
def test_decision_status_outside_accepted_or_proposed_raises_shape_error(value: object) -> None:
    payload: JsonObject = {"status": value, "affects": ["records"]}  # type: ignore[dict-item]
    with pytest.raises(RecordShapeError):
        read_architecture_decision(_decision(payload))


@pytest.mark.parametrize("value", ["accepted", "proposed"])
def test_decision_status_is_read_as_recorded(value: str) -> None:
    decision = read_architecture_decision(_decision({"status": value, "affects": ["records"]}))
    assert decision.status == value


def test_decision_status_schema_has_enum_and_no_default() -> None:
    status = json.loads(COMPOSER_SCHEMA.read_text())["types"]["architecture-decision"]["fields"][
        "status"
    ]
    assert status["enum"] == ["accepted", "proposed"]
    assert "default" not in status
    assert "optional" not in status


def test_composer_schema_version_adds_architecture_types() -> None:
    schema = json.loads(COMPOSER_SCHEMA.read_text())
    assert schema["version"] == "1.3.0"


def test_targets_field_is_optional_string_list_on_standing_constraint() -> None:
    constraint = json.loads(SCORE_SCHEMA.read_text())["types"]["standing-constraint"]
    assert constraint["fields"]["targets"] == {"list": {"type": "string"}, "optional": True}


def test_targets_schema_version_is_2_2_0() -> None:
    assert json.loads(SCORE_SCHEMA.read_text())["version"] == "2.2.0"


def test_targets_keep_existing_constraint_fields() -> None:
    constraint = json.loads(SCORE_SCHEMA.read_text())["types"]["standing-constraint"]
    assert {"area", "rule", "check"} <= set(constraint["fields"])
    assert constraint["sections"] == ["Basis"]
