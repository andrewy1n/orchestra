from __future__ import annotations

import pytest

from orchestra.canon.validation import ValidationError


def _config(project, body: str | None = None):
    return project.create(
        record_type="alpha:config",
        subject="web",
        payload={"title": "web", "level": 1},
        body=body,
    )


def test_supersede_refuses_identical_payload_and_body(project):
    record = _config(project, body="notes")
    with pytest.raises(ValidationError) as caught:
        project.supersede(record["id"], payload={"title": "web", "level": 1}, body="notes")
    assert record["id"] in str(caught.value)
    assert "web" in str(caught.value)


def test_supersede_refuses_when_no_changes_are_given(project):
    record = _config(project)
    with pytest.raises(ValidationError, match=record["id"]):
        project.supersede(record["id"])


def test_supersede_refuses_partial_payload_that_changes_nothing(project):
    record = _config(project)
    with pytest.raises(ValidationError, match=record["id"]):
        project.supersede(record["id"], payload={"level": 1})


def test_supersede_refuses_and_leaves_store_unchanged(project):
    record = _config(project)
    with pytest.raises(ValidationError):
        project.supersede(record["id"])
    assert project.get(record["id"]) == record
    assert project.list("alpha:config") == [record]


def test_supersede_writes_successor_when_payload_differs(project):
    record = _config(project)
    result = project.supersede(record["id"], payload={"level": 2})
    assert result["record"]["payload"]["level"] == 2
    assert result["record"]["id"] != record["id"]
    assert project.resolve("config", "web")["id"] == result["record"]["id"]


def test_supersede_writes_successor_when_body_differs(project):
    record = _config(project, body="old")
    result = project.supersede(record["id"], body="new")
    assert result["record"]["body"].strip() == "new"
    assert result["record"]["id"] != record["id"]
