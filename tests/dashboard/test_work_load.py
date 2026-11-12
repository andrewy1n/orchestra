from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path

import pytest
from canon_support import make_project
from fastapi.testclient import TestClient

from dashboard.backend import phase as phase_mod
from dashboard.backend import snapshot as snapshot_mod
from dashboard.backend.hub import build_hub
from dashboard.backend.phase import PhaseEvidence
from dashboard.backend.server import schemas, service
from dashboard.backend.server.app import create_app
from dashboard.backend.task import TaskRow
from orchestra.canon import project as project_mod
from orchestra.canon import record as record_mod
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record

NOW = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)


class Clock:
    @staticmethod
    def now(_tz: tzinfo | None = None) -> datetime:
        return NOW


def _create(
    project: Project, record_type: str, subject: str, payload: JsonObject, body: str | None = None
) -> Record:
    if body is None:
        body = "\n\n".join(
            f"## {section}\n\nText." for section in project.schemas().types[record_type].sections
        )
    return project.create(record_type=record_type, subject=subject, payload=payload, body=body)


def _phase(project: Project, effort: str, subject: str, done: bool = False) -> Record:
    phase = _create(
        project,
        "score:phase",
        subject,
        {"effort": effort, "title": subject, "ordinal": 1, "weight": "light"},
        "## Problem\n\nP\n\n## Approach\n\nA\n\n## Exit criteria\n\nE\n\n"
        "## Requirements\n\nR1: Behavior.\n",
    )
    phase = project.update(phase["id"], transition="in_progress")
    return project.update(phase["id"], transition="done") if done else phase


@pytest.fixture()
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Project:
    moment = NOW - timedelta(days=10)

    def now() -> str:
        nonlocal moment
        moment += timedelta(seconds=1)
        return moment.isoformat()

    monkeypatch.setattr(record_mod, "now", now)
    monkeypatch.setattr(project_mod, "now", now)
    monkeypatch.setattr(service, "datetime", Clock)
    project = make_project(tmp_path)
    _create(project, "score:effort", "dormant", {"goal": "Sleep", "kind": "deliver"})
    _create(project, "composer:idea", "dormant-idea", {"effort": "dormant", "status": "open"})
    moment = NOW - timedelta(hours=1)
    for effort in ("alpha", "finished", "pending", "empty", "withdrawn"):
        _create(project, "score:effort", effort, {"goal": effort, "kind": "repair"})
        _create(project, "composer:idea", f"{effort}-idea", {"effort": effort, "status": "open"})
    _phase(project, "alpha", "active")
    _phase(project, "alpha", "past", done=True)
    _phase(project, "finished", "finished-phase", done=True)
    _phase(project, "pending", "pending-past", done=True)
    _create(
        project,
        "score:work-item",
        "unphased",
        {"title": "Pending", "effort": "pending", "kind": "repair", "assignee": "", "phase": ""},
    )
    withdrawn = _phase(project, "withdrawn", "withdrawn-phase")
    project.update(withdrawn["id"], transition="withdrawn")
    task = _create(
        project,
        "score:work-item",
        "withdrawn-task",
        {"title": "Old", "effort": "withdrawn", "kind": "repair", "assignee": "", "phase": ""},
    )
    project.update(task["id"], transition="withdrawn")
    running = _create(
        project,
        "score:work-item",
        "running-task",
        {"title": "Run", "effort": "alpha", "kind": "repair", "assignee": "", "phase": "active"},
    )
    project.update(running["id"], transition="in_progress")
    acceptance = _create(
        project,
        "score:acceptance",
        "running-task",
        {
            "effort": "alpha",
            "phase": "active",
            "method": "check",
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    _create(
        project,
        "tuner:check-run",
        "running-task",
        {
            "effort": "alpha",
            "criterion_id": acceptance["id"],
            "revision": "abc",
            "result": "pass",
            "method": "check",
            "signed_by": "",
        },
    )
    _create(
        project,
        "score:continuity-question",
        "alpha",
        {"owner": "user", "blocking": True, "scope": "plan"},
    )
    _create(
        project, "score:effort", "legacy", {"goal": "Old", "kind": "deliver", "status": "closed"}
    )
    _create(
        project,
        "score:effort",
        "renamed",
        {"goal": "New", "kind": "deliver", "merged_from": ["legacy"]},
    )
    _phase(project, "legacy", "legacy-phase")
    _create(project, "composer:idea", "legacy-idea", {"effort": "legacy", "status": "open"})
    _create(project, "composer:idea", "promoted-idea", {"effort": "alpha", "status": "promoted"})
    _create(
        project, "score:effort", "closed", {"goal": "Closed", "kind": "deliver", "status": "closed"}
    )
    _create(project, "composer:idea", "closed-idea", {"effort": "closed", "status": "open"})
    return project


def test_work_data_matches_the_full_snapshot_hub(project: Project) -> None:
    full = snapshot_mod.load_snapshot(project, NOW)
    expected = schemas.HubResponse.model_validate(build_hub(full, NOW))
    reader = service.Reader(project)
    actual = reader.hub()
    compact = reader.cache.work_current(NOW)
    for effort in compact.efforts:
        source = next(item for item in full.efforts if item.effort == effort.effort)
        assert effort.needs_you == source.needs_you
        assert effort.backlog == source.backlog
    assert actual == expected
    assert {item.subject for item in actual.active_phases} == {"active", "legacy-phase"}
    assert {item.effort for item in actual.open_ideas} == {
        "alpha",
        "pending",
        "empty",
        "withdrawn",
        "renamed",
    }


def test_work_request_avoids_full_snapshot_and_finished_phase_work(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    reads = 0
    original_records = Project.records
    original_evidence = snapshot_mod.phase_evidence
    original_tasks = snapshot_mod.task_rows
    phases: list[str] = []

    def records(target: Project) -> list[Record]:
        nonlocal reads
        reads += 1
        return original_records(target)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Work loads full snapshot data")

    def active_task_rows(
        records: list[Record],
        assignments: list[Record] | None = None,
        amendments: list[Record] | None = None,
        reports: list[Record] | None = None,
        checks: list[Record] | None = None,
        phases: list[Record] | None = None,
    ) -> list[TaskRow]:
        assert all(
            record["payload"].get("phase") in ("active", "legacy-phase") for record in records
        )
        return original_tasks(records, assignments, amendments, reports, checks, phases)

    def evidence(
        phase: str,
        effort: str,
        specs: list[Record],
        designs: list[Record],
        decisions: list[Record],
        tasks: list[Record],
        acceptances: list[Record],
        checks: list[Record],
        assessments: list[Record],
        reports: list[Record],
        releases: list[Record],
        phase_records: list[Record] | None = None,
    ) -> PhaseEvidence | None:
        assert phase in ("active", "legacy-phase")
        phases.append(phase)
        return original_evidence(
            phase,
            effort,
            specs,
            designs,
            decisions,
            tasks,
            acceptances,
            checks,
            assessments,
            reports,
            releases,
            phase_records,
        )

    monkeypatch.setattr(Project, "records", records)
    monkeypatch.setattr(service, "load_snapshot", forbidden)
    monkeypatch.setattr(snapshot_mod, "_activity", forbidden)
    monkeypatch.setattr(snapshot_mod, "load_journal", forbidden)
    monkeypatch.setattr(snapshot_mod, "task_rows", active_task_rows)
    monkeypatch.setattr(phase_mod, "task_rows", forbidden)
    monkeypatch.setattr(snapshot_mod, "phase_evidence", evidence)
    response = TestClient(create_app(project)).get("/api/hub")
    assert response.status_code == 200, response.text
    assert reads == 1
    assert sorted(phases) == ["active", "legacy-phase"]


@pytest.mark.parametrize("method", ["records", "derived"])
def test_work_required_record_read_failure_is_visible(
    project: Project, monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    def fail(_target: Project, *_args: object) -> list[Record]:
        raise StoreError("required read failed")

    monkeypatch.setattr(Project, method, fail)
    response = TestClient(create_app(project), raise_server_exceptions=False).get("/api/hub")
    assert response.status_code == 404
    assert "required read failed" in response.text


def test_work_request_completes_while_a_full_snapshot_build_is_blocked(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = service.Reader(project)
    started, release, work_ready = threading.Event(), threading.Event(), threading.Event()
    original = service.load_snapshot

    def load(target: Project, token: str) -> snapshot_mod.Snapshot:
        started.set()
        assert release.wait(10)
        return original(target, token=token)

    def work() -> schemas.HubResponse:
        result = reader.hub()
        work_ready.set()
        return result

    monkeypatch.setattr(service, "load_snapshot", load)
    with ThreadPoolExecutor(max_workers=2) as pool:
        snapshot = pool.submit(reader.snapshot)
        assert started.wait(10)
        hub = pool.submit(work)
        try:
            assert work_ready.wait(3), "Work waits for the full snapshot build"
        finally:
            release.set()
        assert hub.result(timeout=10).generated_at is not None
        snapshot.result(timeout=10)


def test_work_cache_renders_recency_at_the_current_request_time(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = service.Reader(project)
    first = reader.hub()
    later = NOW + timedelta(days=1)

    class LaterClock:
        @staticmethod
        def now(_tz: tzinfo | None = None) -> datetime:
            return later

    monkeypatch.setattr(service, "datetime", LaterClock)
    second = reader.hub()
    assert second.generated_at == later
    assert [item.subject for item in second.open_ideas] == [
        item.subject for item in first.open_ideas
    ]
    assert [item.reason for item in second.open_ideas] != [item.reason for item in first.open_ideas]


def test_work_cache_refreshes_after_a_store_write(project: Project) -> None:
    reader = service.Reader(project)
    first = reader.hub()
    added = _create(project, "composer:idea", "new-idea", {"effort": "alpha", "status": "open"})
    second = reader.hub()
    assert added["id"] not in {item.subject for item in first.open_ideas}
    assert added["id"] in {item.subject for item in second.open_ideas}


def test_concurrent_work_requests_share_one_compact_build(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader = service.Reader(project)
    original = service.load_work_snapshot
    started, following = threading.Event(), threading.Event()
    builds = 0

    def load(target: Project, now: datetime, token: str) -> snapshot_mod.Snapshot:
        nonlocal builds
        builds += 1
        started.set()
        assert following.wait(10)
        return original(target, now=now, token=token)

    def follow() -> schemas.HubResponse:
        following.set()
        return reader.hub()

    monkeypatch.setattr(service, "load_work_snapshot", load)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(reader.hub)
        assert started.wait(10)
        second = pool.submit(follow)
        assert first.result(timeout=10) == second.result(timeout=10)
    assert builds == 1


def test_compact_work_preserves_needs_records_and_task_event_timestamps(project: Project) -> None:
    acceptance = project.resolve("score:acceptance", "running-task")
    unsigned: list[Record] = []
    for subject in ("unsigned", "corrected"):
        unsigned.append(
            _create(
                project,
                "tuner:check-run",
                subject,
                {
                    "effort": "alpha",
                    "criterion_id": acceptance["id"],
                    "revision": "abc",
                    "result": "pass",
                    "method": "manual",
                    "signed_by": "",
                },
            )
        )
    project.correct(unsigned[1]["id"], payload={"signed_by": "reviewer"})
    _create(
        project,
        "tuner:finding",
        "needs-human",
        {
            "effort": "alpha",
            "claim": "Review",
            "basis": "Evidence",
            "invalidated_when": "Resolved",
            "needs": "human",
        },
    )
    _create(
        project,
        "conductor:assessment",
        "active-R1",
        {
            "effort": "alpha",
            "phase": "active",
            "requirement": "R1",
            "status": "blocked",
            "next": "specify",
            "confidence": "low",
        },
    )
    _create(
        project,
        "conductor:integration-report",
        "active",
        {"effort": "alpha", "phase": "active", "result": "fail", "revision": "abc"},
    )
    _create(
        project,
        "conductor:assignment",
        "assigned",
        {"effort": "alpha", "work_item": "running-task", "executor": "agent"},
    )
    report = _create(
        project,
        "conductor:execution-report",
        "reported",
        {
            "effort": "alpha",
            "work_item": "running-task",
            "result": "pass",
            "verdict": "pass",
            "revision": "abc",
        },
    )
    full = snapshot_mod.load_snapshot(project, NOW)
    compact = snapshot_mod.load_work_snapshot(project, NOW)
    full_effort = next(e for e in full.efforts if e.effort == "alpha")
    work_effort = next(e for e in compact.efforts if e.effort == "alpha")
    assert work_effort.needs_you == full_effort.needs_you
    assert {need.kind for need in work_effort.needs_you} == {
        "blocking-question",
        "needs-human",
        "unsigned-check",
        "loop-route",
        "integration",
    }
    assert unsigned[0]["id"] in {need.id for need in work_effort.needs_you}
    assert unsigned[1]["id"] not in {need.id for need in work_effort.needs_you}
    active = next(p for p in work_effort.phases if p.subject == "active")
    assert active.updated_at == datetime.fromisoformat(report["recorded_at"])
    assert build_hub(compact, NOW) == build_hub(full, NOW)
