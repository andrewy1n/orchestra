from __future__ import annotations

import itertools

from orchestra.canon.types import JsonObject, Record
from orchestra.score.planning.analyze import analyze_phase

_CLOCK = itertools.count()


def _record(
    record_type: str,
    subject: str,
    payload: JsonObject,
    *,
    state: str = "active",
    wave: int | None = None,
) -> Record:
    index = next(_CLOCK)
    record: Record = {
        "id": f"<{record_type}:{subject}-{index}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{index}",
        "recorded_at": f"2026-11-01T00:00:{index:02d}Z",
        "body": "## Requirements\n\nR1: One.\n",
    }
    if wave is not None:
        record["derived"] = {"wave": wave}
    return record


def _records(executor: str) -> list[Record]:
    return [
        _record("score:phase", "p", {"weight": "light"}, state="in_progress"),
        _record(
            "score:work-item",
            "small",
            {"phase": "p", "size": "XS", "executor": executor},
            state="planned",
            wave=1,
        ),
        _record(
            "score:work-item",
            "other",
            {"phase": "p", "size": "XS", "estimate_minutes": 8},
            state="planned",
            wave=1,
        ),
        _record("score:acceptance", "R1", {"phase": "p", "requirement": "R1"}),
    ]


def test_analyzer_warns_when_written_executor_differs_from_wave_prediction() -> None:
    report = analyze_phase(_records("subagent"), "p")

    finding = next(f for f in report.findings if f.code == "executor-override-differs")
    assert finding.severity == "warning"
    assert finding.subject == "small"
    assert "subagent" in finding.message
    assert "inline" in finding.message


def test_analyzer_keeps_matching_executor_override_without_warning() -> None:
    report = analyze_phase(_records("inline"), "p")

    assert "executor-override-differs" not in {finding.code for finding in report.findings}


def test_analyzer_uses_only_planned_members_for_override_prediction() -> None:
    records = [
        _record("score:phase", "p", {"weight": "light"}, state="in_progress"),
        _record(
            "score:work-item",
            "completed-large",
            {"phase": "p", "size": "M"},
            state="done",
            wave=1,
        ),
        _record(
            "score:work-item",
            "planned-small",
            {"phase": "p", "size": "XS", "executor": "inline"},
            state="planned",
            wave=1,
        ),
        _record("score:acceptance", "R1", {"phase": "p", "requirement": "R1"}),
    ]

    report = analyze_phase(records, "p")

    assert "executor-override-differs" not in {finding.code for finding in report.findings}


def test_analyzer_keeps_conflicting_wave_overrides_as_an_error() -> None:
    records = _records("inline")
    records[2]["payload"]["executor"] = "subagent"

    report = analyze_phase(records, "p")

    assert any(f.code == "executor-wave-invalid" and f.severity == "error" for f in report.findings)


def test_analyzer_does_not_emit_retired_solo_subagent_warning() -> None:
    records = [
        _record("score:phase", "p", {"weight": "light"}, state="in_progress"),
        _record(
            "score:work-item",
            "solo",
            {"phase": "p", "size": "S", "executor": "subagent"},
            state="planned",
            wave=1,
        ),
        _record("score:acceptance", "R1", {"phase": "p", "requirement": "R1"}),
    ]

    report = analyze_phase(records, "p")

    assert "small-subagent-solo-wave" not in {finding.code for finding in report.findings}
