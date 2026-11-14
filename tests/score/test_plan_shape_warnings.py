from __future__ import annotations

import itertools

from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.score.analyze import analyze_phase

_CLOCK = itertools.count()
_SHAPE_CODES = {
    "task-split-candidate",
    "estimate-outside-size-band",
    "small-subagent-solo-wave",
}


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


def _phase() -> Record:
    body = "## Requirements\n\nR1: One.\n"
    return _record("score:phase", "p", {"weight": "light"}, body, "in_progress")


def _item(subject: str, state: str = "planned", **payload: JsonValue) -> Record:
    return _record(
        "score:work-item",
        subject,
        {"phase": "p", "requirements": ["R1"], **payload},
        state=state,
    )


def _shape(*items: Record, stage: str = "plan") -> set[tuple[str, str]]:
    acceptance = _record("score:acceptance", "a", {"phase": "p", "requirement": "R1"})
    report = analyze_phase([_phase(), *items, acceptance], "p", stage)
    assert all(f.severity == "warning" for f in report.findings if f.code in _SHAPE_CODES)
    return {(f.code, f.subject) for f in report.findings if f.code in _SHAPE_CODES}


def _pair() -> tuple[Record, Record]:
    return (
        _item("a", executor="subagent", size="M", estimate_minutes=10),
        _item("b", executor="subagent", size="M", estimate_minutes=10),
    )


def test_tasks_without_size_get_no_shape_warning() -> None:
    assert _shape(_item("a"), _item("b", depends_on=["a"])) == set()


def test_parallel_medium_subagent_tasks_get_no_shape_warning() -> None:
    assert _shape(*_pair()) == set()


def test_xl_task_is_a_split_candidate() -> None:
    task = _item("a", executor="inline", size="XL", estimate_minutes=30)
    assert _shape(task) == {("task-split-candidate", "a")}


def test_task_with_more_than_four_requirements_is_a_split_candidate() -> None:
    task = _item("a", executor="inline", requirements=["R1", "R2", "R3", "R4", "R5"])
    assert ("task-split-candidate", "a") in _shape(task)


def test_estimate_above_the_size_band_is_reported() -> None:
    a, b = _pair()
    a["payload"]["estimate_minutes"] = 90
    assert _shape(a, b) == {("estimate-outside-size-band", "a")}


def test_estimate_below_the_size_band_is_reported() -> None:
    a, b = _pair()
    a["payload"]["estimate_minutes"] = 3
    assert _shape(a, b) == {("estimate-outside-size-band", "a")}


def test_small_subagent_task_alone_in_its_wave_is_reported() -> None:
    task = _item("a", executor="subagent", size="S", estimate_minutes=6)
    assert _shape(task) == {("small-subagent-solo-wave", "a")}


def test_missing_executor_counts_as_subagent() -> None:
    task = _item("a", size="XS", estimate_minutes=3)
    assert _shape(task) == {("small-subagent-solo-wave", "a")}


def test_small_inline_task_alone_in_its_wave_is_not_reported() -> None:
    task = _item("a", executor="inline", size="S", estimate_minutes=6)
    assert _shape(task) == set()


def test_small_subagent_tasks_that_share_a_wave_are_not_reported() -> None:
    a = _item("a", executor="subagent", size="S", estimate_minutes=6)
    b = _item("b", executor="subagent", size="S", estimate_minutes=6)
    assert _shape(a, b) == set()


def test_small_subagent_task_behind_a_dependency_is_alone_in_its_wave() -> None:
    a = _item("a", executor="inline", size="M", estimate_minutes=10)
    b = _item("b", executor="subagent", size="S", estimate_minutes=6, depends_on=["a"])
    c = _item("c", executor="inline", size="M", estimate_minutes=10, depends_on=["b"])
    assert _shape(a, b, c) == {("small-subagent-solo-wave", "b")}


def test_closing_verification_task_is_not_reported_as_solo() -> None:
    a, b = _pair()
    closing = _item(
        "verify-p", executor="subagent", size="S", estimate_minutes=6, depends_on=["a", "b"]
    )
    assert _shape(a, b, closing) == set()


def test_done_tasks_get_no_shape_warning() -> None:
    task = _item("a", state="done", executor="subagent", size="XL", estimate_minutes=90)
    assert _shape(task) == set()


def test_dependency_cycle_does_not_hang_the_analysis() -> None:
    a = _item("a", executor="inline", size="M", estimate_minutes=10, depends_on=["b"])
    b = _item("b", executor="inline", size="M", estimate_minutes=10, depends_on=["a"])
    assert _shape(a, b) == set()


def test_shape_warnings_are_plan_stage_only() -> None:
    task = _item("a", executor="subagent", size="XL", estimate_minutes=90)
    assert _shape(task, stage="close") == set()
