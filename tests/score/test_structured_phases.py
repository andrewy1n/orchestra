from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.score.phase import structured_phases


def _record(record_type: str, subject: str, payload: JsonObject, state: str, n: int) -> Record:
    return {
        "id": f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:00:{n:02d}Z",
    }


def _spec(subject: str, payload: JsonObject, state: str = "active", n: int = 0) -> Record:
    return _record("score:specification", subject, payload, state, n)


def _phase(subject: str, effort: str, weight: str | None, n: int = 0) -> Record:
    payload: JsonObject = {"title": subject, "ordinal": 1, "effort": effort}
    if weight is not None:
        payload["weight"] = weight
    return _record("score:phase", subject, payload, "planned", n)


def test_structured_phases_collect_effort_and_phase_of_live_specifications() -> None:
    specs = [
        _spec("a-spec", {"effort": "e1", "phase": "p1"}, n=1),
        _spec("b-spec", {"effort": "e2", "phase": "p2"}, n=2),
    ]
    assert structured_phases(specs, []) == {("e1", "p1"), ("e2", "p2")}


def test_structured_phases_skip_dead_and_incomplete_specifications() -> None:
    specs = [
        _spec("old", {"effort": "e1", "phase": "p1"}, state="superseded", n=1),
        _spec("gone", {"effort": "e1", "phase": "p2"}, state="retracted", n=2),
        _spec("no-effort", {"phase": "p3"}, n=3),
        _spec("no-phase", {"effort": "e1"}, n=4),
    ]
    assert structured_phases(specs, []) == set()


def test_structured_phases_include_light_phases_without_a_specification() -> None:
    phases = [_phase("light-one", "e1", "light", 1), _phase("full-one", "e1", "full", 2)]
    assert structured_phases([], phases) == {("e1", "light-one")}


def test_structured_phases_ignore_phases_without_a_weight() -> None:
    assert structured_phases([], [_phase("plain", "e1", None)]) == set()
