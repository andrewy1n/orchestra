from __future__ import annotations

import pytest

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import JsonObject, Record
from orchestra.score.acceptance import Acceptance, read_acceptance
from orchestra.score.requirements import (
    Requirement,
    acceptance_requirement_ids,
    read_requirements,
)

ACCEPTANCE: JsonObject = {
    "effort": "ef",
    "method": "tdd",
    "verify_command": "pytest -q",
}
BODY = "## Problem\nP.\n\n## Requirements\n\nR1: first\nR2: second\n\n## Approach\nA.\n"


def _record(
    payload: JsonObject, record_type: str = "score:acceptance", body: str | None = None
) -> Record:
    record = Record(
        id="rec-1",
        record_type=record_type,
        subject="subject",
        payload=payload,
        lifecycle_state="active",
        relationships={},
        revision="sha256:1",
        recorded_at="2026-01-01T00:00:00Z",
    )
    if body is not None:
        record["body"] = body
    return record


def _without(payload: JsonObject, field: str) -> JsonObject:
    return {key: value for key, value in payload.items() if key != field}


def _assert_names(caught: pytest.ExceptionInfo[RecordShapeError], field: str) -> None:
    assert (caught.value.record_id, caught.value.field) == ("rec-1", field)
    assert "rec-1" in str(caught.value) and field in str(caught.value)


@pytest.mark.parametrize("field", ["effort", "method", "verify_command"])
def test_r13_acceptance_malformed_by_missing_required_field_names_record_and_field(
    field: str,
) -> None:
    with pytest.raises(RecordShapeError) as caught:
        read_acceptance(_record(_without(ACCEPTANCE, field)))

    _assert_names(caught, field)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("effort", 1),
        ("method", "review"),
        ("method", None),
        ("verify_command", ["pytest"]),
        ("phase", 2),
        ("oracle_policy", "strict"),
        ("oracle_policy", 1),
        ("criterion", 3),
        ("requirement", 4),
        ("requirements", "R1"),
        ("requirements", ["R1", 2]),
    ],
)
def test_r13_acceptance_malformed_by_wrong_typed_field_names_record_and_field(
    field: str, value: object
) -> None:
    payload = {**ACCEPTANCE, field: value}

    with pytest.raises(RecordShapeError) as caught:
        read_acceptance(_record(payload))

    _assert_names(caught, field)


def test_r13_requirements_malformed_by_non_string_body_names_record_and_body() -> None:
    record = _record({}, "score:specification")
    record["body"] = 5  # pyright: ignore[reportGeneralTypeIssues] -- deliberately malformed

    with pytest.raises(RecordShapeError) as caught:
        read_requirements(record)

    _assert_names(caught, "body")


def test_r13_requirements_malformed_by_unreadable_requirement_line_names_record_and_body() -> None:
    record = _record({}, "score:specification", "## Requirements\n\nR1 first\n")

    with pytest.raises(RecordShapeError) as caught:
        read_requirements(record)

    _assert_names(caught, "body")


def test_r14_acceptance_reads_optional_fields_as_absent() -> None:
    record = _record(ACCEPTANCE)

    assert read_acceptance(record) == Acceptance(
        id="rec-1",
        subject="subject",
        phase=None,
        effort="ef",
        requirements=(),
        method="tdd",
        oracle_policy=None,
        verify_command="pytest -q",
        criteria=None,
        record=record,
    )


def test_r14_acceptance_reads_blank_optional_fields_as_absent() -> None:
    record = _record({**ACCEPTANCE, "phase": "", "criterion": "", "requirement": ""})

    acceptance = read_acceptance(record)

    assert (acceptance.phase, acceptance.criteria, acceptance.requirements) == (None, None, ())


def test_r14_acceptance_reads_present_optional_fields() -> None:
    record = _record(
        {
            **ACCEPTANCE,
            "phase": "ph",
            "oracle_policy": "frozen",
            "criterion": "it works",
            "requirements": ["R1", "R2"],
        }
    )

    assert read_acceptance(record) == Acceptance(
        id="rec-1",
        subject="subject",
        phase="ph",
        effort="ef",
        requirements=("R1", "R2"),
        method="tdd",
        oracle_policy="frozen",
        verify_command="pytest -q",
        criteria="it works",
        record=record,
    )


@pytest.mark.parametrize(
    "extra",
    [
        {},
        {"requirement": "R3"},
        {"requirements": ["R1", "R2"]},
        {"requirements": ["R1"], "requirement": "R9"},
        {"requirements": [], "requirement": "R9"},
    ],
)
def test_r14_acceptance_requirements_match_acceptance_requirement_ids(
    extra: JsonObject,
) -> None:
    record = _record({**ACCEPTANCE, **extra})

    assert read_acceptance(record).requirements == tuple(acceptance_requirement_ids(record))


def test_r14_requirements_read_ids_and_text_from_the_body() -> None:
    record = _record({}, "score:specification", BODY)

    assert read_requirements(record) == (
        Requirement("R1", "first"),
        Requirement("R2", "second"),
    )


def test_r14_requirements_of_a_record_without_a_body_are_empty() -> None:
    assert read_requirements(_record({}, "score:specification")) == ()
