from __future__ import annotations

import json
from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra.canon.validation import ValidationError

SCHEMA = Path(__file__).resolve().parent.parent / "orchestra/conductor/schemas/conductor.json"
CAUSES = ["spec-gap", "verification-miss", "requirement-change"]


@pytest.fixture
def project(tmp_path: Path):
    project = make_project(tmp_path)
    seed_effort(project)
    return project


def _link(project, subject: str = "fix-1", **overrides):
    payload = {"fix": "fix: repair x", "cause": "spec-gap", "phase": "p1", "effort": "alpha"}
    payload.update(overrides)
    assert "conductor:repair-link" in project.schemas().types
    return create(project, "conductor:repair-link", subject, payload)


def test_links_name_fix_phase_cause(project) -> None:
    _link(project, cause="verification-miss")
    assert project.validate() == []
    record = project.list("conductor:repair-link")[0]["payload"]
    assert record["fix"] == "fix: repair x"
    assert record["phase"] == "p1"
    assert record["cause"] == "verification-miss"


def test_links_are_event_records(project) -> None:
    types = json.loads(SCHEMA.read_text())["types"]
    assert types.get("repair-link", {}).get("lifecycle") == "event"


@pytest.mark.parametrize("cause", CAUSES)
def test_cause_enum_accepts_each_cause(project, cause: str) -> None:
    _link(project, cause=cause)
    assert project.validate() == []


def test_cause_enum_has_three_causes_and_no_phase(project) -> None:
    fields = json.loads(SCHEMA.read_text())["types"].get("repair-link", {}).get("fields", {})
    assert set(fields.get("cause", {}).get("enum", [])) == {*CAUSES, "no-phase"}


def test_no_phase_mark_needs_no_phase_reference(project) -> None:
    create(project, "conductor:repair-link", "fix-1", {"fix": "fix: repair x", "cause": "no-phase"})
    assert project.validate() == []
    assert project.list("conductor:repair-link")[0]["payload"]["cause"] == "no-phase"


def test_rejects_unknown_cause(project) -> None:
    with pytest.raises(ValidationError):
        _link(project, cause="bad-luck")


def test_rejects_unknown_phase(project) -> None:
    with pytest.raises(ValidationError):
        _link(project, phase="no-such-phase")
