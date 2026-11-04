from __future__ import annotations

import json

import pytest

from orchestra.canon.backend import open_backend
from orchestra.canon.cli import EXIT_VALIDATION
from orchestra.canon.types import Record
from orchestra.canon.validation import ValidationError


def _config(project, subject: str = "web", level: int = 1) -> Record:
    return project.create(
        record_type="alpha:config", subject=subject, payload={"title": subject, "level": level}
    )


def test_create_refuses_second_active_current(project):
    _config(project)
    with pytest.raises(ValidationError):
        _config(project, level=2)
    assert len(project.list("alpha:config")) == 1


def test_refusal_names_id_and_supersede(project):
    first = _config(project)
    with pytest.raises(ValidationError) as caught:
        _config(project, level=2)
    message = str(caught.value)
    assert first["id"] in message
    assert f"canon supersede --id {first['id']}" in message


def test_cli_refusal_exits_with_validation_code(cli, project):
    first = _config(project)
    result = cli(
        "create",
        "--type",
        "alpha:config",
        "--subject",
        "web",
        "--payload",
        json.dumps({"title": "again", "level": 2}),
    )
    assert result.code == EXIT_VALIDATION
    assert first["id"] in result.out + result.err


def test_validate_flags_duplicate_active_current(project):
    first = _config(project)
    duplicate: Record = {**first, "id": open_backend(project.store_path).new_id()}
    open_backend(project.store_path).create_record(duplicate)
    errors = [e for e in project.validate() if "multiple active" in e]
    assert len(errors) == 1
    assert first["id"] in errors[0]
    assert duplicate["id"] in errors[0]


def test_supersede_and_other_subjects_still_work(project):
    first = _config(project)
    result = project.supersede(first["id"], payload={"level": 2})
    assert result["record"]["lifecycle_state"] == "active"
    assert result["predecessor"]["lifecycle_state"] == "superseded"
    assert _config(project, subject="api")["lifecycle_state"] == "active"
    assert project.validate() == []


def test_non_current_types_may_repeat_a_subject(project):
    for _ in range(2):
        project.create(record_type="alpha:task", subject="t", payload={"title": "t"})
    assert len(project.list("alpha:task")) == 2
