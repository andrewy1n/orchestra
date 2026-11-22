from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.tuner import schemas
from orchestra.tuner.evidence_facts import finding_basis
from orchestra.tuner.record_facts import (
    RecordShapeError,
    check_run_facts,
    finding_facts,
)

CHECK_REQUIRED = ("criterion_id", "revision", "result", "method", "signed_by")
FINDING_REQUIRED = ("claim", "basis", "needs")


def _record(record_type: str, payload: JsonObject, record_id: str = "<rec:1>") -> Record:
    return {
        "id": record_id,
        "record_type": record_type,
        "subject": "s",
        "payload": payload,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00Z",
    }


def _check_payload() -> JsonObject:
    return {
        "criterion_id": "<acc:1>",
        "revision": "abc1234",
        "result": "pass",
        "method": "check",
        "signed_by": "",
        "effort": "e",
    }


def _finding_payload() -> JsonObject:
    return {"claim": "c", "basis": "b", "needs": "none", "effort": "e"}


def _declared(record_type: str) -> dict[str, JsonObject]:
    path = Path(schemas.__file__).with_name("tuner.json")
    document = json.loads(path.read_text(encoding="utf-8"))
    fields: dict[str, JsonObject] = document["types"][record_type]["fields"]
    return fields


def test_schema_marks_the_strict_check_run_fields_required() -> None:
    fields = _declared("check-run")
    assert all(not fields[name].get("optional") for name in CHECK_REQUIRED)
    assert fields["requirement"]["optional"] is True
    assert fields["evidence_kind"]["optional"] is True


def test_schema_marks_the_strict_finding_fields_required() -> None:
    fields = _declared("finding")
    assert all(not fields[name].get("optional") for name in FINDING_REQUIRED)


def test_valid_check_run_reads_every_field() -> None:
    payload = _check_payload()
    payload["requirement"] = "R1"
    payload["evidence_kind"] = "unit"
    facts = check_run_facts(_record("tuner:check-run", payload, "<cr:9>"))
    assert (facts.id, facts.criterion_id, facts.revision) == ("<cr:9>", "<acc:1>", "abc1234")
    assert (facts.result, facts.method, facts.signed_by) == ("pass", "check", "")
    assert (facts.requirement, facts.evidence_kind) == ("R1", "unit")


def test_optional_check_run_fields_keep_empty_defaults() -> None:
    facts = check_run_facts(_record("tuner:check-run", _check_payload()))
    assert facts.requirement == ""
    assert facts.evidence_kind == ""


@pytest.mark.parametrize("field", ["requirement", "evidence_kind"])
def test_optional_check_run_field_with_a_wrong_type_keeps_the_empty_default(
    field: str,
) -> None:
    payload = _check_payload()
    payload[field] = 7
    assert getattr(check_run_facts(_record("tuner:check-run", payload)), field) == ""


@pytest.mark.parametrize("field", CHECK_REQUIRED)
def test_check_run_missing_a_required_field_raises_naming_record_and_field(field: str) -> None:
    payload = _check_payload()
    del payload[field]
    with pytest.raises(RecordShapeError) as caught:
        check_run_facts(_record("tuner:check-run", payload, "<cr:bad>"))
    assert caught.value.record_id == "<cr:bad>"
    assert caught.value.field == field
    assert "<cr:bad>" in str(caught.value)
    assert field in str(caught.value)


@pytest.mark.parametrize("field", CHECK_REQUIRED)
@pytest.mark.parametrize("bad", [None, 3, ["x"], {"a": 1}])
def test_check_run_with_an_ill_typed_required_field_raises(field: str, bad: JsonValue) -> None:
    payload = _check_payload()
    payload[field] = bad
    with pytest.raises(RecordShapeError) as caught:
        check_run_facts(_record("tuner:check-run", payload, "<cr:bad>"))
    assert (caught.value.record_id, caught.value.field) == ("<cr:bad>", field)


def test_check_run_with_a_non_object_payload_raises() -> None:
    record = _record("tuner:check-run", {})
    record["payload"] = "nope"  # pyright: ignore[reportGeneralTypeIssues]
    with pytest.raises(RecordShapeError):
        check_run_facts(record)


def test_empty_signed_by_is_a_valid_unsigned_check_run() -> None:
    assert check_run_facts(_record("tuner:check-run", _check_payload())).signed_by == ""


def test_record_shape_error_is_a_value_error() -> None:
    assert issubclass(RecordShapeError, ValueError)


def test_valid_finding_reads_claim_needs_and_basis() -> None:
    record = _record("tuner:finding", _finding_payload())
    facts = finding_facts(record)
    assert (facts.claim, facts.needs) == ("c", "none")
    assert finding_basis(record) == "b"


@pytest.mark.parametrize("field", ["claim", "needs"])
def test_finding_missing_a_required_field_raises_naming_record_and_field(field: str) -> None:
    payload = _finding_payload()
    del payload[field]
    with pytest.raises(RecordShapeError) as caught:
        finding_facts(_record("tuner:finding", payload, "<f:bad>"))
    assert (caught.value.record_id, caught.value.field) == ("<f:bad>", field)


@pytest.mark.parametrize("field", ["claim", "needs"])
@pytest.mark.parametrize("bad", [None, 3, ["x"]])
def test_finding_with_an_ill_typed_required_field_raises(field: str, bad: JsonValue) -> None:
    payload = _finding_payload()
    payload[field] = bad
    with pytest.raises(RecordShapeError) as caught:
        finding_facts(_record("tuner:finding", payload, "<f:bad>"))
    assert (caught.value.record_id, caught.value.field) == ("<f:bad>", field)


def test_finding_basis_missing_raises_naming_record_and_field() -> None:
    payload = _finding_payload()
    del payload["basis"]
    with pytest.raises(RecordShapeError) as caught:
        finding_basis(_record("tuner:finding", payload, "<f:bad>"))
    assert (caught.value.record_id, caught.value.field) == ("<f:bad>", "basis")


@pytest.mark.parametrize("bad", [None, 4, ["x"]])
def test_finding_basis_ill_typed_raises(bad: JsonValue) -> None:
    payload = _finding_payload()
    payload["basis"] = bad
    with pytest.raises(RecordShapeError):
        finding_basis(_record("tuner:finding", payload, "<f:bad>"))


def test_empty_finding_basis_is_a_valid_text() -> None:
    payload = _finding_payload()
    payload["basis"] = ""
    assert finding_basis(_record("tuner:finding", payload)) == ""
