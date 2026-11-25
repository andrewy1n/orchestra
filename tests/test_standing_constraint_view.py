from __future__ import annotations

import itertools

from orchestra.canon.types import JsonObject, Record
from orchestra.views.render import VERIFICATION, render_view

PHASE = "refunds"
NAME = "stripe-sdk-isolation"
EVIDENCE = "refunds.py:3: import stripe"
_CLOCK = itertools.count()


def _record(
    record_type: str,
    subject: str,
    payload: JsonObject,
    state: str = "recorded",
    body: str | None = None,
) -> Record:
    n = next(_CLOCK)
    record: Record = {
        "id": f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:00:{n:02d}Z",
    }
    if body is not None:
        record["body"] = body
    return record


def _requirement_records() -> list[Record]:
    acceptance = _record(
        "score:acceptance",
        "refund-api",
        {
            "phase": PHASE,
            "effort": "e",
            "requirement": "R1",
            "method": "check",
            "verify_command": "true",
        },
        "active",
    )
    run = _record(
        "tuner:check-run",
        "refund-api",
        {
            "criterion_id": acceptance["id"],
            "result": "pass",
            "revision": "abc",
            "method": "check",
            "signed_by": "",
        },
    )
    spec = _record(
        "score:specification",
        f"{PHASE}-spec",
        {"phase": PHASE, "requirements": ["R1"]},
        "active",
    )
    return [spec, acceptance, run]


def _constraint(name: str = NAME) -> Record:
    return _record(
        "score:standing-constraint",
        name,
        {"area": "payments", "rule": "Only billing adapters import Stripe.", "check": "true"},
        "active",
    )


def _design(*pinned: Record) -> Record:
    return _record(
        "score:design",
        f"{PHASE}-design",
        {"phase": PHASE, "effort": "e", "standing_constraints": [c["id"] for c in pinned]},
        "active",
    )


def _constraint_run(constraint: Record, result: str, body: str | None = None) -> Record:
    return _record(
        "tuner:check-run",
        f"{constraint['subject']}-check",
        {
            "criterion_id": f"standing-constraint:{constraint['id']}",
            "result": result,
            "revision": "abc",
            "method": "check",
            "runner": "orchestra",
            "effort": "e",
            "signed_by": "",
        },
        body=body,
    )


def _view(records: list[Record]) -> str:
    return render_view(VERIFICATION, records)


def _block(text: str) -> str:
    assert "### Standing constraints\n" in text
    return text.split("### Standing constraints\n", 1)[1].split("\n###", 1)[0]


def test_violated_constraint_listed_beside_verified_requirement() -> None:
    constraint = _constraint()
    run = _constraint_run(constraint, "fail", EVIDENCE)
    text = _view([*_requirement_records(), constraint, _design(constraint), run])

    assert "- **R1**: verified" in text
    assert text.index("### Requirements") < text.index("### Standing constraints")
    block = _block(text)
    assert f"- **{NAME}** (payments): violated" in block
    assert constraint["id"] in block
    assert run["id"] in block
    assert EVIDENCE in block


def test_verified_constraint_shows_outcome_and_check_run() -> None:
    constraint = _constraint()
    run = _constraint_run(constraint, "pass")
    block = _block(_view([*_requirement_records(), constraint, _design(constraint), run]))

    assert f"- **{NAME}** (payments): verified" in block
    assert run["id"] in block


def test_pinned_constraint_without_applicable_check_run_reads_unverified() -> None:
    old = _constraint()
    current = _constraint()
    older_pass = _constraint_run(old, "pass")
    block = _block(_view([*_requirement_records(), old, current, _design(current), older_pass]))

    assert f"- **{NAME}** (payments): unverified" in block
    assert current["id"] in block
    assert older_pass["id"] not in block


def test_no_block_when_phase_pins_nothing() -> None:
    constraint = _constraint()
    text = _view([*_requirement_records(), constraint, _design()])

    assert "- **R1**: verified" in text
    assert "### Standing constraints" not in text


def test_superseded_declaration_shows_newer_version() -> None:
    old = _constraint()
    run = _constraint_run(old, "pass")
    old_inactive: Record = {**old, "lifecycle_state": "superseded"}
    newer = _constraint()
    block = _block(_view([*_requirement_records(), old_inactive, newer, _design(old), run]))

    assert f"- **{NAME}** (payments): verified" in block
    assert old["id"] in block
    assert f" _(newer version: {newer['id']})_" in block
