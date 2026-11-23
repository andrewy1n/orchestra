from __future__ import annotations

from orchestra.canon.types import Record
from orchestra.score.facts.work_item_facts import owning_task_id


def _task(subject: str, state: str, n: int) -> Record:
    return {
        "id": f"<score:work-item:{subject}-{n}>",
        "record_type": "score:work-item",
        "subject": subject,
        "payload": {},
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:00:{n:02d}Z",
    }


def test_owning_task_id_picks_the_longest_live_subject_prefix() -> None:
    short = _task("foo", "planned", 1)
    long = _task("foo-bar", "planned", 2)
    assert owning_task_id("foo-bar-1", [short, long]) == long["id"]
    assert owning_task_id("foo-1", [short, long]) == short["id"]


def test_owning_task_id_matches_the_exact_subject() -> None:
    task = _task("foo", "planned", 1)
    assert owning_task_id("foo", [task]) == task["id"]


def test_owning_task_id_is_empty_without_an_owner() -> None:
    assert owning_task_id("other-1", [_task("foo", "planned", 1)]) == ""
    assert owning_task_id("foobar", [_task("foo", "planned", 1)]) == ""
    assert owning_task_id("foo", []) == ""


def test_owning_task_id_skips_superseded_and_retracted_tasks() -> None:
    live = _task("foo", "planned", 1)
    superseded = _task("foo-bar", "superseded", 2)
    retracted = _task("foo-bar-baz", "retracted", 3)
    assert owning_task_id("foo-bar-baz-1", [live, superseded, retracted]) == live["id"]
