from __future__ import annotations

import pytest

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.conductor.landing.landing import (
    landing_proof_state,
    latest_landing,
    proof_packet,
    read_landing,
    read_proof_packet,
)
from orchestra.score.planning.phase import Phase, read_phase

HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
SAME_TIME = "2026-11-08T10:00:00+00:00"


def _record(
    record_type: str, record_id: str, payload: JsonObject, recorded_at: str, write_order: int = 0
) -> Record:
    return {
        "id": record_id,
        "record_type": record_type,
        "subject": "p1",
        "payload": payload,
        "lifecycle_state": "recorded",
        "relationships": {},
        "revision": "sha256:x",
        "recorded_at": recorded_at,
        "body": "",
        "derived": {"write_order": write_order},
    }


def _landing(
    record_id: str, recorded_at: str = SAME_TIME, write_order: int = 0, **overrides: JsonValue
) -> Record:
    payload: JsonObject = {
        "phase": "p1",
        "number": 7,
        "url": "https://github.com/o/r/pull/7",
        "head_sha": HEAD,
        "result": "success",
    }
    payload.update(overrides)
    return _record("conductor:landing", record_id, payload, recorded_at, write_order)


def _packet(record_id: str, recorded_at: str = SAME_TIME, **overrides: JsonValue) -> Record:
    payload: JsonObject = {"phase": "p1", "revision": HEAD, "base": "main", "kind": "claims"}
    payload.update(overrides)
    return _record("conductor:proof-packet", record_id, payload, recorded_at)


def _with_field(record: Record, field: str, value: JsonValue | None) -> Record:
    payload = {key: item for key, item in record["payload"].items() if key != field}
    if value is not None:
        payload[field] = value
    return {**record, "payload": payload}


def _phase(effort: str = "e1") -> Phase:
    return read_phase(
        {
            "id": "rec-phase",
            "record_type": "score:phase",
            "subject": "p1",
            "payload": {"title": "P one", "ordinal": 1, "effort": effort},
            "lifecycle_state": "active",
            "relationships": {},
            "revision": "sha256:x",
            "recorded_at": "2026-11-01T00:00:00+00:00",
            "body": "",
        }
    )


def test_r6_latest_landing_resolves_equal_recorded_at_by_record_id() -> None:
    low = _landing("rec-a", result="fail")
    high = _landing("rec-b")

    for order in ([low, high], [high, low]):
        found = latest_landing(order, "p1")
        assert found is not None
        assert found.id == "rec-b"
        assert found.result == "success"


def test_r6_latest_landing_prefers_the_later_recorded_at_over_a_higher_id() -> None:
    older = _landing("rec-z", "2026-11-08T09:00:00+00:00")
    newer = _landing("rec-a", "2026-11-08T11:00:00+00:00")

    found = latest_landing([older, newer], "p1")

    assert found is not None
    assert found.id == "rec-a"


def test_r6_latest_landing_ignores_other_phases() -> None:
    other = _landing("rec-z", phase="p2")
    mine = _landing("rec-a")

    found = latest_landing([mine, other], "p1")

    assert found is not None
    assert found.id == "rec-a"


def test_r6_latest_landing_is_none_without_a_landing_for_the_phase() -> None:
    assert latest_landing([_landing("rec-a", phase="p2")], "p1") is None


def test_r6_proof_packet_resolves_equal_recorded_at_by_record_id() -> None:
    low = _packet("rec-a", kind="claims")
    high = _packet("rec-b", kind="full")

    for order in ([low, high], [high, low]):
        found = proof_packet(order, _phase())
        assert found is not None
        assert found.id == "rec-b"
        assert found.kind == "full"


def test_r6_proof_packet_at_head_resolves_equal_recorded_at_by_record_id() -> None:
    low = _packet("rec-a")
    high = _packet("rec-b")

    found = proof_packet([high, low], _phase(), HEAD[:7])

    assert found is not None
    assert found.id == "rec-b"


def test_r6_proof_packet_keeps_the_stored_record_unchanged() -> None:
    record = _packet("rec-a")

    found = proof_packet([record], _phase())

    assert found is not None
    assert found.record is record


def test_r6_landing_proof_state_uses_the_write_order_tiebreak() -> None:
    failed = _landing("rec-b", write_order=1, result="success")
    newest = _landing("rec-a", write_order=2, result="fail")

    assert landing_proof_state([failed, newest, _packet("rec-p")], _phase()) == "failed"


def test_r8_proof_packet_without_effort_reads_with_no_effort() -> None:
    packet = read_proof_packet(_packet("rec-a"))

    assert packet.effort is None
    assert packet.phase == "p1"
    assert packet.revision == HEAD
    assert packet.base == "main"
    assert packet.kind == "claims"
    assert packet.id == "rec-a"
    assert packet.recorded_at == SAME_TIME


def test_r8_proof_packet_without_effort_belongs_to_the_phase_with_its_subject() -> None:
    packet = _packet("rec-a")

    found = proof_packet([packet], _phase("any-effort"))

    assert found is not None
    assert found.id == "rec-a"
    assert found.effort is None


def test_r8_proof_packet_with_another_effort_does_not_belong() -> None:
    assert proof_packet([_packet("rec-a", effort="other")], _phase("e1")) is None


def test_r8_proof_packet_with_the_phase_effort_belongs() -> None:
    found = proof_packet([_packet("rec-a", effort="e1")], _phase("e1"))

    assert found is not None
    assert found.effort == "e1"


def test_r8_proof_packet_of_another_phase_does_not_belong() -> None:
    assert proof_packet([_packet("rec-a", phase="p2")], _phase()) is None


def test_r8_proof_packet_base_is_optional() -> None:
    assert read_proof_packet(_with_field(_packet("rec-a"), "base", None)).base is None


@pytest.mark.parametrize("field", ["phase", "revision", "kind"])
def test_r8_proof_packet_without_a_required_field_names_the_record_and_field(field: str) -> None:
    with pytest.raises(RecordShapeError) as raised:
        read_proof_packet(_with_field(_packet("rec-a"), field, None))

    assert raised.value.record_id == "rec-a"
    assert raised.value.field == field


def test_r9_landing_without_effort_is_a_valid_landing() -> None:
    landing = read_landing(_landing("rec-a"))

    assert landing.effort is None
    assert landing.id == "rec-a"
    assert landing.phase == "p1"
    assert landing.number == 7
    assert landing.url == "https://github.com/o/r/pull/7"
    assert landing.head_sha == HEAD
    assert landing.result == "success"
    assert landing.recorded_at == SAME_TIME


def test_r9_landing_with_an_effort_keeps_it() -> None:
    assert read_landing(_landing("rec-a", effort="e1")).effort == "e1"


def test_r9_landing_keeps_the_stored_record_unchanged() -> None:
    record = _landing("rec-a")

    assert read_landing(record).record is record


def test_r9_landing_without_effort_is_the_latest_landing_of_its_phase() -> None:
    found = latest_landing([_landing("rec-a")], "p1")

    assert found is not None
    assert found.effort is None


def test_r9_landing_without_effort_lands_the_phase() -> None:
    state = landing_proof_state([_landing("rec-a"), _packet("rec-p")], _phase())

    assert state == "landed"


@pytest.mark.parametrize("result", ["success", "fail", "blocked", "skipped"])
def test_r9_landing_accepts_every_result(result: str) -> None:
    assert read_landing(_landing("rec-a", result=result)).result == result


@pytest.mark.parametrize("field", ["phase", "number", "url", "head_sha", "result"])
def test_r9_landing_without_a_required_field_names_the_record_and_field(field: str) -> None:
    with pytest.raises(RecordShapeError) as raised:
        read_landing(_with_field(_landing("rec-a"), field, None))

    assert raised.value.record_id == "rec-a"
    assert raised.value.field == field


@pytest.mark.parametrize(
    ("field", "value"),
    [("number", "7"), ("number", True), ("url", 3), ("result", "merged")],
)
def test_r9_landing_with_a_malformed_field_names_the_record_and_field(
    field: str, value: JsonValue
) -> None:
    with pytest.raises(RecordShapeError) as raised:
        read_landing(_with_field(_landing("rec-a"), field, value))

    assert raised.value.record_id == "rec-a"
    assert raised.value.field == field
