from __future__ import annotations

import cProfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from orchestra import views
from orchestra.canon.project import Project, open_store
from orchestra.canon.types import Record
from orchestra.conductor.head_evidence import EvidenceIndex, acceptance_latest, acceptance_runs
from orchestra.conductor.requirements import requirement_status
from scripts.benchmark_cli import Fixture, build_fixture


class CountedRecords(list[Record]):
    def __init__(self, records: list[Record]) -> None:
        super().__init__(records)
        self.visits = 0

    def __iter__(self) -> Iterator[Record]:
        for record in super().__iter__():
            self.visits += 1
            yield record


@pytest.fixture
def fixture(tmp_path: Path) -> Fixture:
    return build_fixture(tmp_path / "store", 100)


def _project(fixture: Fixture, *, read_only: bool = False) -> Project:
    return open_store(fixture.root, store=fixture.root / ".canon", read_only=read_only)


def test_acceptance_queries_do_not_rescan_unrelated_check_runs(fixture: Fixture) -> None:
    records = _project(fixture, read_only=True).records()
    index = EvidenceIndex(records)
    counted = CountedRecords(index.check_runs)
    index.check_runs = counted
    acceptances = [r for r in records if r["record_type"] == "score:acceptance"]
    for acceptance in acceptances:
        assert len(acceptance_runs(index, acceptance)) == 3
        assert acceptance_latest(index, acceptance, None).holds
    assert counted.visits == 0


def test_requirement_derivation_bounds_full_record_visits(fixture: Fixture) -> None:
    records = CountedRecords(_project(fixture, read_only=True).records())
    statuses = requirement_status(records, "benchmark-phase-000")
    assert len(statuses) == 5
    assert all(status.status == "verified" for status in statuses.values())
    assert records.visits <= 6 * len(records)


@pytest.mark.parametrize("name", ["status", "plan", "verification"])
def test_render_derives_each_phase_requirement_status_once(
    fixture: Fixture, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    records = views.load_records(_project(fixture, read_only=True))
    monkeypatch.chdir(fixture.root)
    profiler = cProfile.Profile()
    text = profiler.runcall(views.render_view, views.VIEWS[name], records)
    calls = sum(
        entry.callcount
        for entry in profiler.getstats()
        if entry.code is requirement_status.__code__
    )
    assert "**R1**: verified" in text
    assert calls == 1


def test_render_reads_a_new_snapshot_after_evidence_changes(fixture: Fixture) -> None:
    project = _project(fixture)
    records = views.load_records(project)
    before = views.render_view(views.VIEWS["status"], records)
    acceptance = next(
        r
        for r in records
        if r["record_type"] == "score:acceptance" and r["payload"].get("requirement") == "R1"
    )
    project.create(
        record_type="tuner:check-run",
        subject="later-failing-run",
        payload={
            "criterion_id": acceptance["id"],
            "revision": "benchmark-revision",
            "result": "fail",
            "effort": "benchmark-effort",
            "method": "check",
            "signed_by": "",
        },
    )
    after = views.render_view(views.VIEWS["status"], views.load_records(project))
    assert "**R1**: verified" in before
    assert "**R1**: failed" in after


def test_evidence_alias_lookup_preserves_input_order_and_duplicate_records(
    fixture: Fixture,
) -> None:
    project = _project(fixture)
    acceptance = next(r for r in project.records() if r["record_type"] == "score:acceptance")
    project.create(
        record_type="tuner:check-run",
        subject="legacy-subject-run",
        payload={
            "criterion_id": acceptance["subject"],
            "revision": "benchmark-revision",
            "result": "pass",
            "effort": "benchmark-effort",
            "method": "check",
            "signed_by": "",
        },
    )
    records = list(reversed(project.records()))
    expected = [
        r
        for r in records
        if r["record_type"] == "tuner:check-run"
        and r["payload"].get("criterion_id") in (acceptance["id"], acceptance["subject"])
    ]
    records.append(expected[0])
    expected.append(expected[0])
    assert acceptance_runs(EvidenceIndex(records), acceptance) == expected
    same_key: Record = {**acceptance, "subject": acceptance["id"]}
    assert acceptance_runs(EvidenceIndex(records), same_key) == [
        r for r in expected if r["payload"].get("criterion_id") == acceptance["id"]
    ]


def test_effort_filtered_render_ignores_another_efforts_correction(fixture: Fixture) -> None:
    project = _project(fixture)
    project.create(
        record_type="score:effort",
        subject="other-effort",
        payload={"goal": "Other work", "kind": "deliver"},
    )
    records = project.records()
    acceptance = next(
        r
        for r in records
        if r["record_type"] == "score:acceptance" and r["payload"].get("requirement") == "R1"
    )
    latest = acceptance_latest(EvidenceIndex(records), acceptance, None).run
    assert latest is not None
    project.correct(latest["id"], payload={"effort": "other-effort", "result": "fail"})
    records = views.load_records(project)
    scoped = views.render_view(views.VIEWS["status"], records, effort="benchmark-effort")
    unscoped = views.render_view(views.VIEWS["status"], records)
    assert "**R1**: verified" in scoped
    assert "**R1**: failed" in unscoped


def test_specification_timestamp_ties_follow_record_id(fixture: Fixture) -> None:
    records = _project(fixture, read_only=True).records()
    specification = next(r for r in records if r["record_type"] == "score:specification")
    first: Record = {
        **specification,
        "id": "z-specification",
        "payload": {**specification["payload"], "requirements": ["R7"]},
    }
    second: Record = {
        **specification,
        "id": "a-specification",
        "payload": {**specification["payload"], "requirements": ["R8"]},
    }
    remaining = [r for r in records if r["record_type"] != "score:specification"]
    assert list(requirement_status([*remaining, first, second], "benchmark-phase-000")) == ["R7"]
    assert list(requirement_status([*remaining, second, first], "benchmark-phase-000")) == ["R7"]


def test_assessment_timestamp_ties_follow_record_id(fixture: Fixture) -> None:
    project = _project(fixture)
    payload = {
        "phase": "benchmark-phase-000",
        "effort": "benchmark-effort",
        "requirement": "R1",
        "next": "execute",
        "confidence": "high",
    }
    body = "## Evidence\n\nWritten assessment.\n\n## Missing\n\nA passing check.\n\n## Reason\n\nFollow up."
    first: Record = project.create(
        record_type="conductor:assessment",
        subject="first-assessment",
        payload={**payload, "status": "failed"},
        body=body,
    )
    second: Record = project.create(
        record_type="conductor:assessment",
        subject="second-assessment",
        payload={**payload, "status": "blocked"},
        body=body,
    )
    stamp = "2026-12-01T00:00:00+00:00"
    first = {**first, "id": "a-assessment", "recorded_at": stamp}
    second = {**second, "id": "z-assessment", "recorded_at": stamp}
    remaining = [r for r in project.records() if r["record_type"] != "conductor:assessment"]
    assert (
        requirement_status([*remaining, first, second], "benchmark-phase-000")["R1"].assessed
        == "blocked"
    )
    assert (
        requirement_status([*remaining, second, first], "benchmark-phase-000")["R1"].assessed
        == "blocked"
    )


@pytest.mark.parametrize("excluded", ["corrected", "superseded"])
def test_requirement_index_uses_current_phase_from_full_snapshot(
    fixture: Fixture, excluded: str
) -> None:
    records = _project(fixture, read_only=True).records()
    phase = next(r for r in records if r["record_type"] == "score:phase")
    first: Record = {
        **phase,
        "id": "a-phase",
        "payload": {**phase["payload"], "weight": "light"},
        "body": "## Requirements\nR7: Current requirement",
    }
    second: Record = {
        **first,
        "id": "z-phase",
        "lifecycle_state": "superseded" if excluded == "superseded" else "in_progress",
        "body": "## Requirements\nR8: Excluded requirement",
    }
    correction: Record = {
        **next(r for r in records if r["record_type"] == "score:specification"),
        "relationships": {"corrects": [second["id"]]} if excluded == "corrected" else {},
    }
    remaining = [r for r in records if r["id"] not in (phase["id"], correction["id"])]
    assert list(
        requirement_status([*remaining, first, second, correction], "benchmark-phase-000")
    ) == ["R7"]


def test_fixture_writes_ignore_parent_store_selection(
    fixture: Fixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = build_fixture(tmp_path / "sentinel", 100)
    sentinel_project = _project(sentinel, read_only=True)
    before = sentinel_project.change_token()
    monkeypatch.setenv("CANON_STORE", str(sentinel.root / ".canon"))
    project = _project(fixture)
    record = project.create(
        record_type="tuner:check-run",
        subject="fixture-only-run",
        payload={
            "criterion_id": "fixture-isolation",
            "revision": "benchmark-revision",
            "result": "pass",
            "effort": "benchmark-effort",
            "method": "check",
            "signed_by": "",
        },
    )
    assert project.get(record["id"])["subject"] == "fixture-only-run"
    assert len(project.records()) == fixture.records + 1
    assert sentinel_project.change_token() == before
    assert len(sentinel_project.records()) == sentinel.records
