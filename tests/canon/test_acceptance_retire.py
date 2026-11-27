from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from canon_support import SCHEMA_PATH, create, make_project, seed_effort  # noqa: E402

from orchestra.canon.lifecycle import LIFECYCLES  # noqa: E402
from orchestra.score.lookups import acceptances_of  # noqa: E402


@pytest.fixture
def project(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("CANON_SCHEMA_PATH", SCHEMA_PATH)
    project = make_project(tmp_path / "store")
    seed_effort(project)
    return project


def _acceptance(project):
    create(
        project,
        "score:work-item",
        "p1-impl",
        {
            "title": "impl",
            "phase": "p1",
            "kind": "deliver",
            "assignee": "agent",
            "effort": "alpha",
        },
    )
    return create(
        project,
        "score:acceptance",
        "p1-impl",
        {
            "criterion": "c",
            "method": "check",
            "phase": "p1",
            "effort": "alpha",
            "verify_command": "true",
        },
    )


def _gate_acceptances(project) -> list[str]:
    records = project.records()
    work_items = [r for r in records if r["record_type"] == "score:work-item"]
    acceptances = [r for r in records if r["record_type"] == "score:acceptance"]
    item = work_items[0]
    return [a["id"] for a in acceptances_of("p1", item, work_items, acceptances)]


def test_retirable_lifecycle_allows_retired_and_superseded_from_active():
    assert "retirable" in LIFECYCLES
    lifecycle = LIFECYCLES["retirable"]
    assert lifecycle.initial == "active"
    assert lifecycle.allows("active", "retired")
    assert lifecycle.allows("active", "superseded")
    assert not lifecycle.allows("retired", "active")
    assert not lifecycle.allows("retired", "superseded")


def test_acceptance_moves_to_retired_through_update(project):
    record = _acceptance(project)
    result = project.update(record["id"], transition="retired")
    assert result["lifecycle_state"] == "retired"


def test_retired_acceptance_does_not_reach_the_gate(project):
    record = _acceptance(project)
    assert _gate_acceptances(project) == [record["id"]]
    project.update(record["id"], transition="retired")
    assert _gate_acceptances(project) == []


def test_retired_acceptance_stays_readable_in_history(project):
    record = _acceptance(project)
    project.update(record["id"], transition="retired")
    states = [change["lifecycle_state"] for change in project.history(record["id"])]
    assert states == ["active", "retired"]
    assert project.get(record["id"])["lifecycle_state"] == "retired"


def test_active_acceptance_still_supersedes(project):
    record = _acceptance(project)
    result = project.supersede(record["id"], payload={"criterion": "replaced"})
    assert result["predecessor"]["lifecycle_state"] == "superseded"
    assert result["record"]["lifecycle_state"] == "active"
