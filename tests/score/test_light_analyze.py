from __future__ import annotations

import itertools

from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.score.analyze import analyze_phase

_CLOCK = itertools.count()


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
        "recorded_at": f"2026-11-01T00:00:{n:02d}Z",
        "body": body,
    }


_BODY = "## Requirements\n\nR1: One.\nR2: Two.\n"


def _phase(weight: str, body: str = _BODY) -> Record:
    return _record("score:phase", "p", {"weight": weight}, body, "in_progress")


def _item(*requirements: str) -> Record:
    return _record(
        "score:work-item",
        "t",
        {"phase": "p", "requirements": list(requirements)},
        state="planned",
    )


def _acceptance(**requirement: JsonValue) -> Record:
    return _record("score:acceptance", "t", {"phase": "p", **requirement})


def _codes(records: list[Record], severity: str = "error") -> set[str]:
    report = analyze_phase(records, "p")
    return {f.code for f in report.findings if f.severity == severity}


def test_light_phase_passes_without_specification_or_design() -> None:
    records = [_phase("light"), _item("R1", "R2"), _acceptance(requirements=["R1", "R2"])]
    assert _codes(records) == set()


def test_light_phase_reports_a_requirement_with_no_acceptance() -> None:
    records = [_phase("light"), _item("R1", "R2"), _acceptance(requirement="R1")]
    assert _codes(records) == {"requirement-no-acceptance"}


def test_light_phase_reports_an_unknown_acceptance_id() -> None:
    records = [
        _phase("light"),
        _item("R1", "R2"),
        _acceptance(requirements=["R1", "R2", "R9"]),
    ]
    assert _codes(records) == {"acceptance-unknown-requirement"}


def test_full_phase_requires_an_active_specification() -> None:
    assert _codes([_phase("full"), _item("R1"), _acceptance(requirement="R1")]) == {
        "active-specification-required"
    }


def test_full_phase_multi_requirement_acceptance_is_an_error() -> None:
    spec = _record("score:specification", "p", {"phase": "p", "requirements": ["R1", "R2"]}, _BODY)
    records = [
        _phase("full"),
        spec,
        _item("R1", "R2"),
        _acceptance(requirements=["R1", "R2"]),
    ]
    assert "full-phase-multi-requirement" in _codes(records)


def test_full_phase_empty_requirements_list_names_none_and_defers_to_requirement() -> None:
    spec = _record("score:specification", "p", {"phase": "p", "requirements": ["R1"]}, _BODY)
    records = [
        _phase("full"),
        spec,
        _item("R1"),
        _acceptance(requirements=[], requirement="R1"),
    ]
    codes = _codes(records)
    assert "full-phase-multi-requirement" not in codes
    assert "requirement-no-acceptance" not in codes


def _light_body_codes(body: str) -> set[str]:
    return _codes([_phase("light", body), _item("R1"), _acceptance(requirement="R1")])


def test_light_phase_rejects_a_malformed_requirement_line() -> None:
    assert "light-requirements-invalid" in _light_body_codes(
        "## Requirements\n\nR1: One.\nR2 - Two.\n"
    )


def test_light_phase_rejects_a_missing_requirements_section() -> None:
    assert "light-requirements-invalid" in _light_body_codes("## Problem\n\nNothing.\n")


def test_light_phase_rejects_an_empty_requirements_section() -> None:
    assert "light-requirements-invalid" in _light_body_codes("## Requirements\n\nNone yet.\n")


def test_light_phase_rejects_a_duplicate_requirement_id() -> None:
    assert "light-requirements-invalid" in _light_body_codes(
        "## Requirements\n\nR1: One.\nR1: Again.\n"
    )


def test_light_phase_rejects_a_requirement_with_no_text() -> None:
    assert "light-requirements-invalid" in _light_body_codes("## Requirements\n\nR1:\n")
