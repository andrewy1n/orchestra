from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import make_project

from orchestra.canon import record as record_mod
from orchestra.canon.project import Project
from orchestra.canon.sqlite_backend import SqliteBackend
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.verification.evidence.head_evidence import EvidenceIndex, acceptance_latest

STAMP = "2026-11-01T00:00:00+00:00"
HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"


def _run(project: Project, acceptance: Record, name: str, result: str) -> Record:
    payload: JsonObject = {
        "criterion_id": acceptance["id"],
        "revision": HEAD,
        "result": result,
        "effort": "e",
        "method": "check",
        "signed_by": "",
        "requirement": "R1",
    }
    return project.create(record_type="tuner:check-run", subject=name, payload=payload)


@pytest.fixture()
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Project:
    monkeypatch.setattr(record_mod, "now", lambda: STAMP)
    store = make_project(tmp_path)
    ids = iter(f"rec-00000000-0000-4000-8000-{n:012d}" for n in range(999, 0, -1))
    monkeypatch.setattr(SqliteBackend, "new_id", lambda self: next(ids))
    return store


def _sectioned(project: Project, record_type: str) -> str:
    return "\n\n".join(
        f"## {name}\n\nText." for name in project.schemas().types[record_type].sections
    )


def _acceptance(project: Project) -> Record:
    project.create(
        record_type="score:effort",
        subject="e",
        payload={"goal": "Ship", "kind": "deliver"},
        body=_sectioned(project, "score:effort"),
    )
    project.create(
        record_type="score:phase",
        subject="p",
        payload={"title": "p", "ordinal": 1, "effort": "e", "weight": "light"},
        body="## Problem\n\nP\n\n## Approach\n\nA\n\n## Exit criteria\n\nE\n\n"
        "## Requirements\n\nR1: First.\n",
    )
    return project.create(
        record_type="score:acceptance",
        subject="p-R1",
        payload={
            "method": "check",
            "phase": "p",
            "effort": "e",
            "verify_command": "true",
            "requirement": "R1",
        },
        body=_sectioned(project, "score:acceptance"),
    )


def test_same_second_check_runs_take_the_later_written_one(project: Project) -> None:
    acceptance = _acceptance(project)
    earlier = _run(project, acceptance, "first", "pass")
    later = _run(project, acceptance, "second", "fail")
    assert later["id"] < earlier["id"]
    assert later["recorded_at"] == earlier["recorded_at"]

    answer = acceptance_latest(EvidenceIndex(project.records()), acceptance, None)

    assert answer.run is not None
    assert answer.run["id"] == later["id"]
    assert not answer.holds


def test_same_second_check_runs_ignore_the_order_records_are_listed_in(
    project: Project,
) -> None:
    acceptance = _acceptance(project)
    _run(project, acceptance, "first", "pass")
    later = _run(project, acceptance, "second", "fail")
    records = project.records()
    for ordered in (records, list(reversed(records))):
        answer = acceptance_latest(EvidenceIndex(ordered), acceptance, None)
        assert answer.run is not None
        assert answer.run["id"] == later["id"]
