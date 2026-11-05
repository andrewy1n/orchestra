from __future__ import annotations

import itertools
from pathlib import Path

from canon_support import create, make_project

from dashboard.backend.phase import PhaseEvidence, load_requirement_detail, phase_evidence
from orchestra.canon.types import JsonObject, Record

_CLOCK = itertools.count()
_BODY = "## Requirements\n\nR1: First behavior.\nR2: Second behavior.\n"


def _record(
    record_type: str, subject: str, payload: JsonObject, body: str = "", state: str = "active"
) -> Record:
    n = next(_CLOCK)
    return {
        "id": f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:00:{n:02d}+00:00",
        "body": body,
    }


def _evidence(phase_record: Record, results: list[str]) -> PhaseEvidence | None:
    acceptance = _record(
        "score:acceptance",
        "a",
        {"phase": "p", "effort": "e", "requirements": ["R1", "R2"]},
    )
    checks = [
        _record(
            "tuner:check-run",
            "a",
            {"criterion_id": acceptance["id"], "result": result, "effort": "e"},
            state="recorded",
        )
        for result in results
    ]
    return phase_evidence(
        "p", "e", [], [], [], [], [acceptance], checks, [], [], [], [phase_record]
    )


def test_light_phase_requirements_come_from_the_phase_body() -> None:
    phase = _record("score:phase", "p", {"effort": "e", "weight": "light"}, _BODY, "in_progress")
    evidence = _evidence(phase, ["pass"])
    assert evidence is not None
    rows = {row.id: row for row in evidence.requirements}
    assert {rid: row.text for rid, row in rows.items()} == {
        "R1": "First behavior.",
        "R2": "Second behavior.",
    }
    assert {row.status for row in rows.values()} == {"verified"}


def test_light_phase_failing_multi_requirement_check_verifies_no_listed_id() -> None:
    phase = _record("score:phase", "p", {"effort": "e", "weight": "light"}, _BODY, "in_progress")
    evidence = _evidence(phase, ["fail"])
    assert evidence is not None
    assert {row.status for row in evidence.requirements} == {"unassessed"}


def test_full_phase_without_a_specification_has_no_evidence() -> None:
    phase = _record("score:phase", "p", {"effort": "e", "weight": "full"}, _BODY, "in_progress")
    assert _evidence(phase, ["pass"]) is None


def test_light_phase_multi_requirement_check_is_attached_to_each_listed_row() -> None:
    phase = _record("score:phase", "p", {"effort": "e", "weight": "light"}, _BODY, "in_progress")
    evidence = _evidence(phase, ["pass"])
    assert evidence is not None
    attached = {row.id: row.latest_check for row in evidence.requirements}
    assert attached["R1"] is not None
    assert attached["R2"] is not None
    assert attached["R1"].result == "pass"
    assert attached["R2"].result == "pass"


def test_requirement_detail_reads_a_light_phase_body(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", "e", {"goal": "G", "kind": "deliver"})
    create(
        project,
        "score:phase",
        "p",
        {"title": "P", "ordinal": 1, "effort": "e", "weight": "light"},
        "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n\n" + _BODY,
    )
    acceptance = create(
        project,
        "score:acceptance",
        "a",
        {
            "method": "check",
            "phase": "p",
            "effort": "e",
            "verify_command": "true",
            "requirements": ["R1", "R2"],
        },
    )
    create(
        project,
        "tuner:check-run",
        "a",
        {
            "criterion_id": acceptance["id"],
            "revision": "abc",
            "result": "pass",
            "effort": "e",
            "method": "check",
            "signed_by": "",
        },
        "ok",
    )
    detail = load_requirement_detail(project, "e", "p", "R2")
    assert detail.text == "Second behavior."
    assert detail.status == "verified"
