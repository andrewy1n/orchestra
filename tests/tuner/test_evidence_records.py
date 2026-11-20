from __future__ import annotations

import pytest

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import JsonObject, Record
from orchestra.tuner.records import (
    CheckRun,
    EvidenceBinding,
    Finding,
    read_check_run,
    read_evidence_binding,
    read_finding,
)

CHECK_RUN: JsonObject = {
    "criterion_id": "acc-1",
    "revision": "abc123",
    "result": "pass",
    "signed_by": "",
}
FINDING: JsonObject = {
    "claim": "c",
    "basis": "b",
    "invalidated_when": "i",
    "effort": "ef",
    "needs": "n",
}
BINDING: JsonObject = {
    "observation_id": "obs-1",
    "claim_id": "claim-1",
    "base_rev": "base",
    "head_rev": "head",
}


def _record(record_type: str, payload: JsonObject) -> Record:
    return Record(
        id="rec-1",
        record_type=record_type,
        subject="subject",
        payload=payload,
        lifecycle_state="active",
        relationships={},
        revision="sha256:1",
        recorded_at="2026-01-01T00:00:00Z",
    )


def _check_run(payload: JsonObject) -> Record:
    return _record("tuner:check-run", payload)


def _finding(payload: JsonObject) -> Record:
    return _record("tuner:finding", payload)


def _binding(payload: JsonObject) -> Record:
    return _record("tuner:evidence-binding", payload)


def _without(payload: JsonObject, field: str) -> JsonObject:
    return {key: value for key, value in payload.items() if key != field}


def _with(payload: JsonObject, field: str, value: object) -> JsonObject:
    changed = dict(payload)
    changed[field] = value  # pyright: ignore[reportArgumentType] -- deliberately malformed
    return changed


def _assert_names(caught: pytest.ExceptionInfo[RecordShapeError], field: str) -> None:
    assert (caught.value.record_id, caught.value.field) == ("rec-1", field)
    assert "rec-1" in str(caught.value) and field in str(caught.value)


@pytest.mark.parametrize("field", ["criterion_id", "revision", "result", "signed_by"])
def test_r13_check_run_malformed_by_missing_required_field_names_record_and_field(
    field: str,
) -> None:
    with pytest.raises(RecordShapeError) as caught:
        read_check_run(_check_run(_without(CHECK_RUN, field)), 0)

    _assert_names(caught, field)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("criterion_id", 5),
        ("revision", None),
        ("result", "maybe"),
        ("result", 1),
        ("signed_by", ["a"]),
    ],
)
def test_r13_check_run_malformed_by_wrong_typed_field_names_record_and_field(
    field: str, value: object
) -> None:
    with pytest.raises(RecordShapeError) as caught:
        read_check_run(_check_run(_with(CHECK_RUN, field, value)), 0)

    _assert_names(caught, field)


@pytest.mark.parametrize("field", ["claim", "basis", "invalidated_when", "effort", "needs"])
def test_r13_finding_malformed_by_missing_required_field_names_record_and_field(
    field: str,
) -> None:
    with pytest.raises(RecordShapeError) as caught:
        read_finding(_finding(_without(FINDING, field)))

    _assert_names(caught, field)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("claim", 1),
        ("needs", None),
        ("phase", 3),
        ("severity", ["high"]),
        ("resolution_note", 2),
        ("contradicted_by", "fnd-1"),
        ("contradicted_by", ["fnd-1", 4]),
    ],
)
def test_r13_finding_malformed_by_wrong_typed_field_names_record_and_field(
    field: str, value: object
) -> None:
    with pytest.raises(RecordShapeError) as caught:
        read_finding(_finding(_with(FINDING, field, value)))

    _assert_names(caught, field)


@pytest.mark.parametrize("field", ["observation_id", "claim_id", "base_rev", "head_rev"])
def test_r13_evidence_binding_malformed_by_missing_required_field_names_record_and_field(
    field: str,
) -> None:
    with pytest.raises(RecordShapeError) as caught:
        read_evidence_binding(_binding(_without(BINDING, field)))

    _assert_names(caught, field)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("observation_id", 1),
        ("head_rev", None),
        ("effort", 2),
        ("retired", "yes"),
        ("retired", 1),
    ],
)
def test_r13_evidence_binding_malformed_by_wrong_typed_field_names_record_and_field(
    field: str, value: object
) -> None:
    with pytest.raises(RecordShapeError) as caught:
        read_evidence_binding(_binding(_with(BINDING, field, value)))

    _assert_names(caught, field)


def test_r14_check_run_reads_required_fields_and_write_order_without_optional_fields() -> None:
    record = _check_run(CHECK_RUN)

    assert read_check_run(record, 7) == CheckRun(
        id="rec-1",
        criterion_id="acc-1",
        result="pass",
        revision="abc123",
        signed_by="",
        recorded_at="2026-01-01T00:00:00Z",
        write_order=7,
        record=record,
    )


def test_r14_check_run_ignores_absent_and_present_optional_fields_alike() -> None:
    full = _check_run(
        {
            **CHECK_RUN,
            "method": "tdd",
            "effort": "ef",
            "exit_code": 1,
            "duration_s": 1.5,
            "failing_node_ids": ["t::a"],
        }
    )

    assert read_check_run(full, 0).criterion_id == "acc-1"


def test_r14_finding_leaves_absent_optional_fields_empty() -> None:
    record = _finding(FINDING)

    assert read_finding(record) == Finding(
        id="rec-1",
        claim="c",
        basis="b",
        invalidated_when="i",
        effort="ef",
        needs="n",
        phase=None,
        resolution_note=None,
        severity=None,
        contradicted_by=(),
        record=record,
    )


def test_r14_finding_reads_blank_optional_fields_as_absent() -> None:
    finding = read_finding(_finding({**FINDING, "phase": "", "resolution_note": ""}))

    assert (finding.phase, finding.resolution_note) == (None, None)


def test_r14_finding_reads_present_optional_fields() -> None:
    finding = read_finding(
        _finding(
            {
                **FINDING,
                "phase": "ph",
                "resolution_note": "done",
                "severity": "high",
                "contradicted_by": ["fnd-2"],
            }
        )
    )

    assert (finding.phase, finding.resolution_note, finding.severity) == ("ph", "done", "high")
    assert finding.contradicted_by == ("fnd-2",)


def test_r14_evidence_binding_leaves_absent_optional_fields_empty() -> None:
    record = _binding(BINDING)

    assert read_evidence_binding(record) == EvidenceBinding(
        id="rec-1",
        observation_id="obs-1",
        claim_id="claim-1",
        base_rev="base",
        head_rev="head",
        effort=None,
        retired=False,
        record=record,
    )


def test_r14_evidence_binding_reads_present_optional_fields() -> None:
    binding = read_evidence_binding(_binding({**BINDING, "effort": "ef", "retired": True}))

    assert (binding.effort, binding.retired) == ("ef", True)
