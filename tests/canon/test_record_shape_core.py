from __future__ import annotations

import json

import pytest
from conftest import PLAN_BODY, make_task

from orchestra.canon.errors import RecordShapeError, StoreError
from orchestra.canon.index import RecordIndex
from orchestra.canon.sections import body_section, body_sections
from orchestra.canon.types import Record


@pytest.fixture
def ready(cli, project):
    return cli


def _full_list(ready, record_type: str) -> dict[str, dict]:
    listed = ready.ok("list", "--type", record_type, "--full")
    return {
        record["id"]: {k: v for k, v in record.items() if k != "derived"}
        for record in listed["records"]
    }


def test_r13_get_and_list_return_a_superseded_record_unchanged(ready):
    first = ready.ok(
        "create", "--type", "beta:plan", "--subject", "p", "--set", 'goal="g"', "--body", PLAN_BODY
    )["record"]
    result = ready.ok("supersede", "--type", "plan", "--subject", "p", "--set", 'goal="h"')
    stored = result["predecessor"]
    assert stored["lifecycle_state"] == "superseded"
    assert stored["body"] == PLAN_BODY
    assert stored["payload"] == {"goal": "g"}

    fetched = ready.ok("get", "--id", first["id"])
    assert fetched == stored
    assert _full_list(ready, "plan")[first["id"]] == stored
    assert ready("get", "--id", first["id"], "--body-only").out == PLAN_BODY + "\n"


def test_r13_get_and_list_return_a_superseding_record_unchanged(ready):
    ready.ok(
        "create", "--type", "beta:plan", "--subject", "p", "--set", 'goal="g"', "--body", PLAN_BODY
    )
    successor = ready.ok("supersede", "--type", "plan", "--subject", "p", "--set", 'goal="h"')[
        "record"
    ]

    assert ready.ok("get", "--id", successor["id"]) == successor
    assert _full_list(ready, "plan")[successor["id"]] == successor


def test_r13_get_and_list_return_a_corrected_record_unchanged(ready, project):
    make_task(project, "t")
    log = ready.ok(
        "create", "--type", "log", "--subject", "t", "--payload", '{"task": "t", "message": "m"}'
    )["record"]
    corrected = ready.ok("correct", "--id", log["id"], "--set", 'message="n"')["record"]

    assert ready.ok("get", "--id", log["id"]) == log
    assert _full_list(ready, "log")[log["id"]] == log
    assert ready.ok("get", "--id", corrected["id"]) == corrected
    assert _full_list(ready, "log")[corrected["id"]] == corrected


def test_r13_get_output_is_the_stored_record_bytes(ready, project):
    first = ready.ok(
        "create", "--type", "beta:plan", "--subject", "p", "--set", 'goal="g"', "--body", PLAN_BODY
    )["record"]
    ready.ok("supersede", "--type", "plan", "--subject", "p", "--set", 'goal="h"')
    stored = project.get(first["id"])
    result = ready("get", "--id", first["id"])
    assert result.code == 0
    assert result.out == json.dumps(stored, indent=2) + "\n"


def test_record_shape_error_names_record_field_and_message():
    error = RecordShapeError("rec-1", "payload.title", "missing")
    assert str(error) == "record rec-1: field payload.title: missing"
    assert (error.record_id, error.field, error.message) == ("rec-1", "payload.title", "missing")
    assert isinstance(error, StoreError)


def test_body_sections_maps_each_level_two_heading_to_its_stripped_text():
    body = "preamble\n\n## One\n\nfirst\n\n## Two  \nsecond\nline\n"
    assert body_sections(body) == {"One": "first", "Two": "second\nline"}


def test_body_sections_ignores_deeper_headings_as_boundaries():
    body = "## One\ntext\n### Deep\nmore\n## Two\nx"
    assert body_sections(body) == {"One": "text\n### Deep\nmore", "Two": "x"}


def test_body_sections_is_empty_without_level_two_headings():
    assert body_sections("") == {}
    assert body_sections("# Title\nplain\n#### Four") == {}


def test_body_sections_first_duplicate_heading_wins():
    assert body_sections("## A\none\n## A\ntwo") == {"A": "one"}


def test_body_section_returns_the_named_text_or_empty():
    body = "## Landing\n\nplace\n\n## Other\n\nz"
    assert body_section(body, "Landing") == "place"
    assert body_section(body, "Missing") == ""
    assert body_section("", "Landing") == ""


def _record(record_id: str, record_type: str, subject: str) -> Record:
    return {
        "id": record_id,
        "record_type": record_type,
        "subject": subject,
        "payload": {},
        "lifecycle_state": "recorded",
        "relationships": {},
        "revision": "",
        "recorded_at": "",
    }


def test_index_of_type_lists_records_in_insertion_order():
    records = [
        _record("a", "x:one", "s1"),
        _record("b", "x:two", "s1"),
        _record("c", "x:one", "s2"),
        _record("d", "x:one", "s1"),
    ]
    index = RecordIndex(records)
    assert [r["id"] for r in index.of_type("x:one")] == ["a", "c", "d"]
    assert [r["id"] for r in index.of_type("x:two")] == ["b"]
    assert index.of_type("x:none") == []


def test_index_of_type_returns_a_copy_the_caller_may_change():
    index = RecordIndex([_record("a", "x:one", "s")])
    index.of_type("x:one").clear()
    assert [r["id"] for r in index.of_type("x:one")] == ["a"]
