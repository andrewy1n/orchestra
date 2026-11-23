from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.verification.requirements import requirement_status
from orchestra.score.lookups import prepare_records

PHASE = "p"
HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"


def _record(
    index: int, record_type: str, subject: str, payload: JsonObject, state: str = "active"
) -> Record:
    return {
        "id": f"rec-{index}",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{index}",
        "recorded_at": f"2026-11-01T00:00:{index:02d}Z",
        "derived": {"write_order": index},
        "body": "",
    }


def _records() -> list[Record]:
    acceptance = _record(
        2,
        "score:acceptance",
        "a-one",
        {
            "phase": PHASE,
            "effort": "e",
            "requirement": "R1",
            "method": "check",
            "verify_command": "true",
        },
    )
    run = _record(
        3,
        "tuner:check-run",
        "a-one",
        {"criterion_id": acceptance["id"], "result": "pass", "revision": HEAD, "signed_by": ""},
        "recorded",
    )
    spec = _record(1, "score:specification", PHASE, {"phase": PHASE, "requirements": ["R1"]})
    phase = _record(0, "score:phase", PHASE, {"effort": "e"}, "in_progress")
    return [phase, spec, acceptance, run]


def test_status_inside_prepared_records_matches_the_unprepared_status() -> None:
    records = _records()
    expected = requirement_status(records, PHASE)
    with prepare_records(records):
        assert requirement_status(records, PHASE) == expected
    assert expected["R1"].status == "verified"


def _without_specification() -> list[Record]:
    records = [record for record in _records() if record["record_type"] != "score:specification"]
    item = _record(
        4,
        "score:work-item",
        "w-one",
        {"phase": PHASE, "effort": "e", "requirements": ["R1"]},
        "planned",
    )
    return [*records, item]


def test_work_item_requirements_inside_prepared_records_match_the_unprepared_status() -> None:
    records = _without_specification()
    expected = requirement_status(records, PHASE)
    with prepare_records(records):
        assert requirement_status(records, PHASE) == expected
    assert list(expected) == ["R1"]


def test_light_phase_requirements_inside_prepared_records_match_the_unprepared_status() -> None:
    records = _records()
    records[0]["payload"] = {"effort": "e", "weight": "light"}
    records[0]["body"] = "## Requirements\n\nR1: the one requirement\n"
    expected = requirement_status(records, PHASE)
    with prepare_records(records):
        assert requirement_status(records, PHASE) == expected
    assert list(expected) == ["R1"]
