from __future__ import annotations

import itertools

from orchestra.canon.types import JsonObject, Record
from orchestra.derive import acceptance_requirement_ids, phase_requirements, phase_weight

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


_REQUIREMENTS = "## Requirements\n\nR1: First behavior.\nR2: Second behavior.\n\n## Proof\n\nR9: not a requirement.\n"


def test_phase_body_requirements_come_from_a_light_phase() -> None:
    phase = _record("score:phase", "p", {"weight": "light"}, _REQUIREMENTS, "in_progress")
    assert phase_weight([phase], "p") == "light"
    assert phase_requirements([phase], "p") == [
        ("R1", "First behavior."),
        ("R2", "Second behavior."),
    ]


def test_phase_body_without_weight_is_full_and_has_no_requirements() -> None:
    phase = _record("score:phase", "p", {}, _REQUIREMENTS, "in_progress")
    assert phase_weight([phase], "p") == "full"
    assert phase_requirements([phase], "p") == []


def test_full_phase_requirements_source_is_the_specification_body() -> None:
    phase = _record("score:phase", "p", {"weight": "full"}, _REQUIREMENTS, "in_progress")
    spec = _record(
        "score:specification", "p", {"phase": "p"}, "## Requirements\n\nR7: From the spec.\n"
    )
    assert phase_requirements([phase, spec], "p") == [("R7", "From the spec.")]


def test_light_phase_requirements_source_ignores_a_specification() -> None:
    phase = _record("score:phase", "p", {"weight": "light"}, _REQUIREMENTS, "in_progress")
    spec = _record(
        "score:specification", "p", {"phase": "p"}, "## Requirements\n\nR7: From the spec.\n"
    )
    assert [rid for rid, _ in phase_requirements([phase, spec], "p")] == ["R1", "R2"]


def test_acceptance_requirement_ids_prefers_the_list() -> None:
    both = _record("score:acceptance", "a", {"requirements": ["R1", "R2"], "requirement": "R3"})
    one = _record("score:acceptance", "b", {"requirement": "R3"})
    none = _record("score:acceptance", "c", {})
    assert acceptance_requirement_ids(both) == ["R1", "R2"]
    assert acceptance_requirement_ids(one) == ["R3"]
    assert acceptance_requirement_ids(none) == []
