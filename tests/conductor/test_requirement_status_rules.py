from __future__ import annotations

import itertools

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.requirements import RequirementStatus, requirement_status

PHASE = "p"
HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
_CLOCK = itertools.count()


def _record(
    record_type: str,
    subject: str,
    payload: JsonObject,
    state: str = "active",
    *,
    body: str = "",
    corrects: str | None = None,
) -> Record:
    n = next(_CLOCK)
    return {
        "id": f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {"corrects": [corrects]} if corrects else {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:{n // 60:02d}:{n % 60:02d}Z",
        "derived": {"write_order": n},
        "body": body,
    }


def _spec(*requirements: str, state: str = "active") -> Record:
    return _record(
        "score:specification",
        PHASE,
        {"phase": PHASE, "requirements": list(requirements)},
        state,
    )


def _acceptance(
    subject: str, requirement: str = "R1", *, method: str = "check", state: str = "active"
) -> Record:
    return _record(
        "score:acceptance",
        subject,
        {
            "phase": PHASE,
            "effort": "e",
            "requirement": requirement,
            "method": method,
            "verify_command": "true",
        },
        state,
    )


def _run(
    acceptance: Record,
    result: str,
    *,
    signed_by: str = "",
    corrects: str | None = None,
    revision: str = HEAD,
) -> Record:
    return _record(
        "tuner:check-run",
        acceptance["subject"],
        {
            "criterion_id": acceptance["id"],
            "result": result,
            "revision": revision,
            "signed_by": signed_by,
        },
        "recorded",
        corrects=corrects,
    )


def _assessment(requirement: str, status: str) -> Record:
    return _record(
        "conductor:assessment",
        PHASE,
        {"phase": PHASE, "requirement": requirement, "status": status},
    )


def _status(records: list[Record], requirement: str = "R1") -> RequirementStatus:
    return requirement_status(records, PHASE)[requirement]


def test_all_acceptances_must_pass_before_the_requirement_is_verified() -> None:
    first = _acceptance("a-one")
    second = _acceptance("a-two")
    records = [_spec("R1"), first, second, _run(first, "pass")]
    assert _status(records).status == "unverified"
    records.append(_run(second, "pass"))
    assert _status(records).status == "verified"


def test_all_acceptances_failing_latest_run_fails_the_requirement() -> None:
    first = _acceptance("a-one")
    second = _acceptance("a-two")
    records = [_spec("R1"), first, second, _run(first, "pass"), _run(second, "fail")]
    assert _status(records).status == "failed"


def test_all_acceptances_use_each_latest_run_not_an_earlier_pass() -> None:
    acceptance = _acceptance("a-one")
    records = [_spec("R1"), acceptance, _run(acceptance, "pass"), _run(acceptance, "fail")]
    assert _status(records).status == "failed"


def test_all_acceptances_count_only_active_ones() -> None:
    live = _acceptance("a-live")
    retired = _acceptance("a-retired", state="superseded")
    records = [_spec("R1"), live, retired, _run(live, "pass")]
    status = _status(records)
    assert status.status == "verified"
    assert status.acceptance_ids == (live["id"],)


def test_corrected_failing_run_is_replaced_by_its_correcting_successor() -> None:
    acceptance = _acceptance("a-one")
    failed = _run(acceptance, "fail")
    records = [_spec("R1"), acceptance, failed, _run(acceptance, "pass", corrects=failed["id"])]
    assert _status(records).status == "verified"


def test_corrected_passing_run_is_replaced_by_its_failing_successor() -> None:
    acceptance = _acceptance("a-one")
    passed = _run(acceptance, "pass")
    records = [_spec("R1"), acceptance, passed, _run(acceptance, "fail", corrects=passed["id"])]
    assert _status(records).status == "failed"


def test_corrected_run_written_last_never_counts_as_latest() -> None:
    acceptance = _acceptance("a-one")
    older_fail = _run(acceptance, "fail")
    newer_pass = _run(acceptance, "pass")
    correction = _record(
        "tuner:check-run",
        "a-one",
        {
            "criterion_id": "<other>",
            "result": "pass",
            "revision": HEAD,
            "signed_by": "",
        },
        "recorded",
        corrects=newer_pass["id"],
    )
    records = [_spec("R1"), acceptance, older_fail, newer_pass, correction]
    status = _status(records)
    assert status.status == "failed"
    assert status.check_run_ids == (older_fail["id"],)


def test_signed_manual_pass_verifies_the_requirement() -> None:
    acceptance = _acceptance("a-manual", method="manual")
    records = [_spec("R1"), acceptance, _run(acceptance, "pass", signed_by="reviewer")]
    assert _status(records).status == "verified"


def test_signed_unsigned_manual_pass_does_not_verify_the_requirement() -> None:
    acceptance = _acceptance("a-manual", method="manual")
    records = [_spec("R1"), acceptance, _run(acceptance, "pass")]
    assert _status(records).status == "unverified"


def test_signed_blank_signature_counts_as_unsigned() -> None:
    acceptance = _acceptance("a-manual", method="manual")
    records = [_spec("R1"), acceptance, _run(acceptance, "pass", signed_by="   ")]
    assert _status(records).status == "unverified"


def test_signed_unsigned_manual_fail_still_fails_the_requirement() -> None:
    acceptance = _acceptance("a-manual", method="manual")
    records = [_spec("R1"), acceptance, _run(acceptance, "fail")]
    assert _status(records).status == "failed"


def test_signed_signature_is_not_required_for_automatic_acceptances() -> None:
    acceptance = _acceptance("a-check", method="check")
    records = [_spec("R1"), acceptance, _run(acceptance, "pass")]
    assert _status(records).status == "verified"


def test_written_assessment_holds_a_non_verified_status() -> None:
    acceptance = _acceptance("a-one")
    records = [_spec("R1"), acceptance, _run(acceptance, "pass")]
    assessment = _assessment("R1", "blocked")
    records.append(assessment)
    status = _status(records)
    assert status.status == "unverified"
    assert status.assessment_id == assessment["id"]
    assert status.assessed == "blocked"


def test_written_assessment_yields_to_a_passing_run_recorded_after_it() -> None:
    acceptance = _acceptance("a-one")
    records = [_spec("R1"), acceptance, _run(acceptance, "pass"), _assessment("R1", "blocked")]
    records.append(_run(acceptance, "pass"))
    status = _status(records)
    assert status.status == "verified"
    assert status.assessment_id is None


def test_written_assessment_holds_against_a_later_failing_run() -> None:
    acceptance = _acceptance("a-one")
    records = [_spec("R1"), acceptance, _run(acceptance, "pass")]
    assessment = _assessment("R1", "insufficient")
    records.append(assessment)
    records.append(_run(acceptance, "fail"))
    status = _status(records)
    assert status.assessment_id == assessment["id"]
    assert status.assessed == "insufficient"


def _same_second(records: list[Record]) -> None:
    for record in records:
        record["recorded_at"] = "2026-11-01T00:00:00Z"


def test_written_assessment_yields_to_a_same_second_pass_written_later() -> None:
    acceptance = _acceptance("a-one")
    assessment = _assessment("R1", "failed")
    run = _run(acceptance, "pass")
    _same_second([assessment, run])
    status = _status([_spec("R1"), acceptance, assessment, run])
    assert status.status == "verified"
    assert status.assessment_id is None


def test_written_assessment_holds_against_a_same_second_pass_written_earlier() -> None:
    acceptance = _acceptance("a-one")
    run = _run(acceptance, "pass")
    assessment = _assessment("R1", "failed")
    _same_second([run, assessment])
    status = _status([_spec("R1"), acceptance, run, assessment])
    assert status.status == "failed"
    assert status.assessment_id == assessment["id"]


def test_same_second_assessments_pick_the_later_written_one() -> None:
    acceptance = _acceptance("a-one")
    later = _assessment("R1", "blocked")
    earlier = _assessment("R1", "failed")
    earlier["id"], later["id"] = "<z>", "<a>"
    earlier["derived"] = {"write_order": 1}
    later["derived"] = {"write_order": 2}
    _same_second([earlier, later])
    status = _status([_spec("R1"), acceptance, earlier, later])
    assert status.assessment_id == later["id"]
    assert status.assessed == "blocked"


def test_written_assessment_that_is_verified_changes_nothing() -> None:
    acceptance = _acceptance("a-one")
    records = [_spec("R1"), acceptance, _assessment("R1", "verified"), _run(acceptance, "pass")]
    status = _status(records)
    assert status.status == "verified"
    assert status.assessment_id is None


def test_full_phase_ids_come_from_the_current_specification() -> None:
    old = _spec("R1", "R2", "R3", state="superseded")
    current = _spec("R1", "R4")
    assert list(requirement_status([old, current], PHASE)) == ["R1", "R4"]


def test_full_phase_ids_prefer_the_specification_over_work_items() -> None:
    item = _record("score:work-item", "t", {"phase": PHASE, "requirements": ["R9"]}, "done")
    assert list(requirement_status([_spec("R1"), item], PHASE)) == ["R1"]


def test_full_phase_ids_fall_back_to_work_items_without_a_specification() -> None:
    item = _record("score:work-item", "t", {"phase": PHASE, "requirements": ["R7"]}, "done")
    assert list(requirement_status([item], PHASE)) == ["R7"]


def test_light_phase_ids_come_from_the_phase_body() -> None:
    phase = _record(
        "score:phase",
        PHASE,
        {"weight": "light"},
        "in_progress",
        body="## Requirements\n\nR1: One.\nR2: Two.\n",
    )
    item = _record("score:work-item", "t", {"phase": PHASE, "requirements": ["R9"]}, "done")
    spec = _spec("R8")
    assert list(requirement_status([phase, item, spec], PHASE)) == ["R1", "R2"]


def test_light_phase_ids_verify_through_acceptances() -> None:
    phase = _record(
        "score:phase",
        PHASE,
        {"weight": "light"},
        "in_progress",
        body="## Requirements\n\nR1: One.\n",
    )
    acceptance = _acceptance("a-one")
    statuses = requirement_status([phase, acceptance, _run(acceptance, "pass")], PHASE)
    assert {rid: s.status for rid, s in statuses.items()} == {"R1": "verified"}
