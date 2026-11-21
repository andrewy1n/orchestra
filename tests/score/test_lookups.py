from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.score.lookups import (
    LIVE_WORK_ITEM_STATES,
    PreparedRecordsError,
    acceptances_of,
    closing_work_item,
    closing_work_items,
    current_phase,
    dependencies,
    live_work_items,
    prepare_records,
    records_of_type,
)


@pytest.fixture()
def project(store_template: Path, tmp_path: Path) -> Project:
    root = tmp_path / "repo"
    shutil.copytree(store_template, root)
    project = open_store(root)
    project.create(
        record_type="score:effort",
        subject="workflow",
        payload={"goal": "Deliver work", "kind": "deliver"},
    )
    return project


_PHASE_BODY = (
    "## Problem\nPlan work.\n\n## Approach\nRun tasks.\n\n## Exit criteria\nComplete work.\n"
)


def _phase(project: Project, subject: str) -> Record:
    return project.create(
        record_type="score:phase",
        subject=subject,
        payload={"title": subject, "ordinal": 1, "effort": "workflow"},
        body=_PHASE_BODY,
    )


def _item(
    project: Project,
    subject: str,
    *,
    phase: str = "feature",
    depends_on: list[str] | None = None,
) -> Record:
    payload: JsonObject = {
        "title": subject,
        "phase": phase,
        "kind": "deliver",
        "assignee": "",
        "effort": "workflow",
    }
    if depends_on is not None:
        payload["depends_on"] = list(depends_on)
    return project.create(
        record_type="score:work-item",
        subject=subject,
        payload=payload,
        body="## Description\nImplement the task.\n",
    )


def _acceptance(project: Project, subject: str, *, phase: str = "feature") -> Record:
    return project.create(
        record_type="score:acceptance",
        subject=subject,
        payload={
            "method": "tdd",
            "phase": phase,
            "effort": "workflow",
            "verify_command": "true",
        },
    )


def _read(project: Project, record_type: str) -> list[Record]:
    return project.list(record_type=record_type)


def _with_payload(record: Record, key: str, value: JsonValue) -> Record:
    payload: JsonObject = {**record["payload"], key: value}
    return {**record, "payload": payload}


def _without_payload(record: Record, key: str) -> Record:
    payload: JsonObject = {k: v for k, v in record["payload"].items() if k != key}
    return {**record, "payload": payload}


def test_r2_latest_unsuperseded_phase_is_current(project: Project) -> None:
    first = _phase(project, "feature")
    successor = project.supersede(first["id"], payload={"title": "Second"})["record"]

    found = current_phase("feature", _read(project, "score:phase"))

    assert found is not None
    assert found["id"] == successor["id"]


def test_r2_corrected_phase_is_not_current(project: Project) -> None:
    original = _phase(project, "feature")
    correction: Record = {
        **original,
        "id": "zzzz",
        "relationships": {"corrects": [original["id"]]},
        "recorded_at": "2099-01-01T00:00:00Z",
    }
    older: Record = {**original, "id": "aaaa", "recorded_at": "2000-01-01T00:00:00Z"}
    corrected_newest: Record = {
        **original,
        "id": "mmmm",
        "recorded_at": "2098-01-01T00:00:00Z",
        "relationships": {},
    }
    records = [older, corrected_newest, {**correction, "relationships": {"corrects": ["mmmm"]}}]

    found = current_phase("feature", records)

    assert found is not None
    assert found["id"] == "zzzz"


def test_r2_other_subjects_and_types_are_ignored(project: Project) -> None:
    _phase(project, "other")
    _item(project, "feature", phase="other")

    assert current_phase("feature", project.records()) is None


def test_r3_only_superseded_records_have_no_current_phase(project: Project) -> None:
    first = _phase(project, "feature")
    project.supersede(first["id"], payload={"title": "Second"})
    superseded = [r for r in _read(project, "score:phase") if r["id"] == first["id"]]

    assert [r["lifecycle_state"] for r in superseded] == ["superseded"]
    assert current_phase("feature", superseded) is None


def test_r3_only_corrected_records_have_no_current_phase(project: Project) -> None:
    original = _phase(project, "feature")
    correction: Record = {
        **original,
        "id": "zzzz",
        "lifecycle_state": "superseded",
        "relationships": {"corrects": [original["id"]]},
    }

    assert current_phase("feature", [original, correction]) is None


def test_r4_unknown_slug_has_no_current_phase(project: Project) -> None:
    _phase(project, "feature")

    assert current_phase("missing", _read(project, "score:phase")) is None
    assert current_phase("feature", []) is None


def test_r5_live_states_are_planned_in_progress_done() -> None:
    assert set(LIVE_WORK_ITEM_STATES) == {"planned", "in_progress", "done"}


def test_r6_live_items_filter_by_state_and_phase(project: Project) -> None:
    _phase(project, "feature")
    _phase(project, "elsewhere")
    planned = _item(project, "planned-item")
    started = _item(project, "started-item")
    project.update(started["id"], transition="in_progress")
    withdrawn = _item(project, "withdrawn-item")
    project.update(withdrawn["id"], transition="withdrawn")
    _item(project, "foreign-item", phase="elsewhere")

    found = live_work_items("feature", _read(project, "score:work-item"))

    assert sorted(r["subject"] for r in found) == ["planned-item", "started-item"]
    assert planned["id"] in {r["id"] for r in found}


def test_r7_dependencies_are_the_string_entries(project: Project) -> None:
    _phase(project, "feature")
    _item(project, "a")
    _item(project, "b")
    item = _item(project, "item", depends_on=["a", "b"])

    assert dependencies(item) == ["a", "b"]


def test_r7_absent_depends_on_is_empty(project: Project) -> None:
    _phase(project, "feature")
    item = _item(project, "item")

    assert dependencies(_without_payload(item, "depends_on")) == []


def test_r7_non_list_depends_on_is_empty(project: Project) -> None:
    _phase(project, "feature")
    item = _item(project, "item")

    assert dependencies(_with_payload(item, "depends_on", "a")) == []


def test_r7_non_string_entries_are_dropped(project: Project) -> None:
    _phase(project, "feature")
    item = _item(project, "item")

    assert dependencies(_with_payload(item, "depends_on", ["a", 1, None, "b"])) == ["a", "b"]


def test_r8_closing_item_names_others_by_subject(project: Project) -> None:
    _phase(project, "feature")
    _item(project, "one")
    _item(project, "two")
    closing = _item(project, "close", depends_on=["one", "two"])

    found = closing_work_item("feature", _read(project, "score:work-item"))

    assert found is not None
    assert found["id"] == closing["id"]


def test_r8_closing_item_names_others_by_id(project: Project) -> None:
    _phase(project, "feature")
    one = _item(project, "one")
    two = _item(project, "two")
    closing = _item(project, "close", depends_on=["one", "two"])
    by_id = _with_payload(closing, "depends_on", [one["id"], two["id"]])
    records = [r for r in _read(project, "score:work-item") if r["id"] != closing["id"]]

    found = closing_work_item("feature", [*records, by_id])

    assert found is not None
    assert found["id"] == closing["id"]


def test_r8_item_missing_a_dependency_is_not_closing(project: Project) -> None:
    _phase(project, "feature")
    _item(project, "one")
    _item(project, "two")
    _item(project, "partial", depends_on=["one"])

    assert closing_work_item("feature", _read(project, "score:work-item")) is None


def test_r8_withdrawn_item_need_not_be_named(project: Project) -> None:
    _phase(project, "feature")
    one = _item(project, "one")
    gone = _item(project, "gone")
    project.update(gone["id"], transition="withdrawn")
    closing = _item(project, "close", depends_on=[one["subject"]])

    found = closing_work_item("feature", _read(project, "score:work-item"))

    assert found is not None
    assert found["id"] == closing["id"]


def test_r9_single_live_item_has_no_closing_item(project: Project) -> None:
    _phase(project, "feature")
    _item(project, "only")

    assert closing_work_item("feature", _read(project, "score:work-item")) is None


def test_r9_single_live_item_among_withdrawn_has_no_closing_item(project: Project) -> None:
    _phase(project, "feature")
    _item(project, "only")
    gone = _item(project, "gone")
    project.update(gone["id"], transition="withdrawn")

    assert closing_work_item("feature", _read(project, "score:work-item")) is None


def _owned(project: Project, item: Record) -> list[str]:
    items = live_work_items("feature", _read(project, "score:work-item"))
    acceptances = _read(project, "score:acceptance")
    return sorted(a["subject"] for a in acceptances_of("feature", item, items, acceptances))


def _two_items_with_acceptances(project: Project) -> tuple[Record, Record]:
    _phase(project, "feature")
    foo = _item(project, "foo")
    foo_bar = _item(project, "foo-bar")
    for subject in ("foo", "foo-1", "foo-bar", "foo-bar-1"):
        _acceptance(project, subject)
    return foo, foo_bar


def test_r10_acceptance_matches_by_equal_subject_or_hyphen_prefix(project: Project) -> None:
    _phase(project, "feature")
    foo = _item(project, "foo")
    for subject in ("foo", "foo-1", "foobar", "other"):
        _acceptance(project, subject)

    assert _owned(project, foo) == ["foo", "foo-1"]


def test_r10_acceptance_of_another_phase_does_not_match(project: Project) -> None:
    _phase(project, "feature")
    _phase(project, "elsewhere")
    foo = _item(project, "foo")
    _acceptance(project, "foo")
    _acceptance(project, "foo-1", phase="elsewhere")

    assert _owned(project, foo) == ["foo"]


def test_r10_superseded_acceptance_does_not_match(project: Project) -> None:
    _phase(project, "feature")
    foo = _item(project, "foo")
    old = _acceptance(project, "foo")
    project.supersede(old["id"], payload={"verify_command": "false"})

    assert _owned(project, foo) == ["foo"]


def test_r11_longest_subject_owns_shared_acceptances(project: Project) -> None:
    foo, foo_bar = _two_items_with_acceptances(project)

    assert _owned(project, foo_bar) == ["foo-bar", "foo-bar-1"]
    assert _owned(project, foo) == ["foo", "foo-1"]


def test_r8_closing_work_items_returns_every_mutually_dependent_item(project: Project) -> None:
    _phase(project, "feature")
    first = _item(project, "first")
    second = _item(project, "second", depends_on=["first"])
    project.update(first["id"], payload={"depends_on": ["second"]})

    found = closing_work_items("feature", _read(project, "score:work-item"))

    assert {record["id"] for record in found} == {first["id"], second["id"]}
    latest_found = closing_work_item("feature", _read(project, "score:work-item"))
    assert latest_found is not None
    assert latest_found["id"] in {first["id"], second["id"]}


def test_r8_closing_work_items_is_empty_without_a_closing_item(project: Project) -> None:
    _phase(project, "feature")
    _item(project, "one")
    _item(project, "two")

    assert closing_work_items("feature", _read(project, "score:work-item")) == []


def test_prepared_read_accepts_the_same_ids_and_rejects_another_sequence(project: Project) -> None:
    _phase(project, "feature")
    records = project.records()
    with prepare_records(records):
        assert records_of_type(list(records), "score:phase")
        with pytest.raises(PreparedRecordsError):
            records_of_type(records[:1], "score:phase")
