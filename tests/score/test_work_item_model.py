from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from orchestra.canon.types import JsonObject, Record
from orchestra.score.work_item import WorkItem, current_work_item, read_work_item


def _record(
    record_id: str,
    *,
    subject: str = "task",
    state: str = "in_progress",
    recorded_at: str = "2026-01-01T00:00:00Z",
    payload: JsonObject | None = None,
    corrects: list[str] | None = None,
    record_type: str = "score:work-item",
) -> Record:
    return {
        "id": record_id,
        "record_type": record_type,
        "subject": subject,
        "payload": payload if payload is not None else {},
        "lifecycle_state": state,
        "relationships": {"corrects": corrects} if corrects else {},
        "revision": f"rev-{record_id}",
        "recorded_at": recorded_at,
    }


def test_r14_read_work_item_exposes_payload_fields() -> None:
    record = _record(
        "wi-1",
        payload={
            "phase": "landing",
            "effort": "code-quality",
            "write_root": "/work/tree",
            "requirements": ["R1", "R2"],
        },
    )

    item = read_work_item(record)

    assert item == WorkItem(
        id="wi-1",
        subject="task",
        lifecycle_state="in_progress",
        phase="landing",
        effort="code-quality",
        write_root="/work/tree",
        requirements=("R1", "R2"),
        record=record,
    )


def test_r14_read_work_item_reads_missing_text_as_empty() -> None:
    item = read_work_item(_record("wi-1"))

    assert (item.phase, item.effort, item.write_root) == ("", "", "")
    assert item.requirements == ()


def test_r14_read_work_item_reads_non_string_text_as_empty() -> None:
    item = read_work_item(
        _record("wi-1", payload={"phase": 3, "effort": None, "write_root": ["x"]})
    )

    assert (item.phase, item.effort, item.write_root) == ("", "", "")


def test_r14_read_work_item_keeps_only_string_requirements() -> None:
    item = read_work_item(_record("wi-1", payload={"requirements": ["R1", 2, None, "R3"]}))

    assert item.requirements == ("R1", "R3")


def test_r14_read_work_item_reads_non_list_requirements_as_empty() -> None:
    item = read_work_item(_record("wi-1", payload={"requirements": "R1"}))

    assert item.requirements == ()


def test_r14_work_item_is_frozen() -> None:
    item = read_work_item(_record("wi-1"))

    with pytest.raises(FrozenInstanceError):
        item.phase = "other"  # pyright: ignore[reportAttributeAccessIssue] -- frozen dataclass assignment is the behavior under test


def test_r14_current_work_item_skips_superseded_version() -> None:
    superseded = _record("wi-old", state="superseded", recorded_at="2026-03-01T00:00:00Z")
    current = _record("wi-new", recorded_at="2026-02-01T00:00:00Z")

    found = current_work_item("task", [superseded, current])

    assert found is not None
    assert found.id == "wi-new"


def test_r14_current_work_item_skips_corrected_version() -> None:
    corrected = _record("wi-bad", recorded_at="2026-03-01T00:00:00Z")
    correction = _record("wi-fix", recorded_at="2026-02-01T00:00:00Z", corrects=["wi-bad"])

    found = current_work_item("task", [corrected, correction])

    assert found is not None
    assert found.id == "wi-fix"


def test_r14_current_work_item_picks_latest_recorded_at() -> None:
    older = _record("wi-z", recorded_at="2026-01-01T00:00:00Z")
    newer = _record("wi-a", recorded_at="2026-02-01T00:00:00Z")

    found = current_work_item("task", [newer, older])

    assert found is not None
    assert found.id == "wi-a"


def test_r14_current_work_item_breaks_recorded_at_tie_by_id() -> None:
    first = _record("wi-a")
    second = _record("wi-b")

    found = current_work_item("task", [second, first])

    assert found is not None
    assert found.id == "wi-b"


def test_r14_current_work_item_with_superseded_corrected_and_current_versions() -> None:
    superseded = _record("wi-1", state="superseded", recorded_at="2026-01-01T00:00:00Z")
    corrected = _record("wi-2", recorded_at="2026-02-01T00:00:00Z")
    correction = _record(
        "wi-3",
        recorded_at="2026-03-01T00:00:00Z",
        corrects=["wi-2"],
        payload={"phase": "landing"},
    )
    later_superseded = _record("wi-4", state="superseded", recorded_at="2026-04-01T00:00:00Z")

    found = current_work_item("task", [superseded, corrected, correction, later_superseded])

    assert found is not None
    assert found.id == "wi-3"
    assert found.phase == "landing"


def test_r14_current_work_item_ignores_other_subjects_and_types() -> None:
    other_subject = _record("wi-other", subject="other", recorded_at="2026-05-01T00:00:00Z")
    other_type = _record("ph-1", record_type="score:phase", recorded_at="2026-05-01T00:00:00Z")
    wanted = _record("wi-1")

    found = current_work_item("task", [other_subject, other_type, wanted])

    assert found is not None
    assert found.id == "wi-1"


def test_r14_current_work_item_is_none_without_current_version() -> None:
    only = _record("wi-1", state="superseded")

    assert current_work_item("task", [only]) is None
    assert current_work_item("task", []) is None
