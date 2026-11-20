from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta, timezone

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend.phase import PhaseRow
from dashboard.backend.snapshot import _phase_updated_at
from dashboard.backend.task import belongs
from orchestra.canon import record_payload
from orchestra.canon.types import JsonObject, Record

PHASE = "build"


def _at(minute: int) -> str:
    return (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minute)).isoformat()


def _record(
    record_id: str,
    record_type: str,
    subject: str,
    minute: int,
    payload: JsonObject,
    *,
    state: str,
) -> Record:
    return {
        "id": record_id,
        "record_type": record_type,
        "subject": subject,
        "lifecycle_state": state,
        "relationships": {},
        "revision": record_id,
        "recorded_at": _at(minute),
        "payload": payload,
    }


def _task(
    task_id: str,
    subject: str,
    state: str,
    minute: int,
    *,
    phase: str = PHASE,
    effort: str = "alpha",
) -> Record:
    return _record(
        task_id,
        "score:work-item",
        subject,
        minute,
        {"phase": phase, "effort": effort},
        state=state,
    )


def _check(check_id: str, subject: str, minute: int, *, effort: str | None = "alpha") -> Record:
    payload: JsonObject = {}
    if effort is not None:
        payload["effort"] = effort
    return _record(check_id, "tuner:check-run", subject, minute, payload, state="recorded")


def _row() -> PhaseRow:
    return PhaseRow("build", "Build", 1, "done", 1, 1, id="phase-1")


def _naive(
    tasks: list[Record],
    checks: list[Record],
    assignments: list[Record] | None = None,
    reports: list[Record] | None = None,
) -> datetime | None:
    row = _row()
    phase_records = [_record("phase-1", "score:phase", PHASE, 1, {}, state="done")]
    members = [task for task in tasks if record_payload(task).get("phase") == row.subject]
    names = {task["id"] for task in members} | {task["subject"] for task in members}
    stamps = [datetime.fromisoformat(str(record["recorded_at"])) for record in phase_records]
    stamps.extend(datetime.fromisoformat(str(task["recorded_at"])) for task in members)
    for record in (*(assignments or []), *(reports or [])):
        if record_payload(record).get("work_item") in names:
            stamps.append(datetime.fromisoformat(str(record["recorded_at"])))
    for task in members:
        stamps.extend(
            datetime.fromisoformat(str(check["recorded_at"]))
            for check in checks
            if belongs(check, task, tasks)
        )
    return max(stamps, default=None)


def _updated(
    tasks: list[Record],
    checks: list[Record],
    assignments: list[Record] | None = None,
    reports: list[Record] | None = None,
) -> datetime | None:
    phase_records = [_record("phase-1", "score:phase", PHASE, 1, {}, state="done")]
    return _phase_updated_at(
        _row(),
        phase_records,
        tasks,
        assignments or [],
        reports or [],
        checks,
    )


def test_phase_updated_at_matches_check_ownership() -> None:
    tasks = [
        _task("t-short", "ship", "done", 2),
        _task("t-long", "ship-ui", "done", 3),
        _task("t-same-late", "ship", "done", 4),
        _task("t-old", "ship-ui-copy", "superseded", 5),
        _task("t-other", "other", "done", 6, phase="other"),
        _task("t-withdrawn", "ship-ui-theme", "withdrawn", 7),
        _task("t-effort", "notes", "done", 8, effort="beta"),
    ]
    checks = [
        _check("c-short", "ship", 10),
        _check("c-long", "ship-ui-panel", 20),
        _check("c-copy", "ship-ui-copy-check", 30),
        _check("c-theme", "ship-ui-theme-check", 40),
        _check("c-effort", "notes-body", 50, effort="beta"),
        _check("c-wrong-effort", "notes-body", 60, effort="alpha"),
        _check("c-missing-effort", "ship-extra", 70, effort=None),
        _check("c-foreign", "foreign", 80),
    ]
    assignments = [
        _record(
            "a1",
            "conductor:assignment",
            "a1",
            15,
            {"work_item": "t-long"},
            state="recorded",
        )
    ]
    reports = [
        _record(
            "r1",
            "conductor:execution-report",
            "r1",
            90,
            {"work_item": "ship"},
            state="recorded",
        )
    ]
    assert _updated(tasks, checks, assignments, reports) == _naive(
        tasks, checks, assignments, reports
    )
    assert _updated(tasks, checks, assignments, reports) == datetime.fromisoformat(_at(90))


def test_phase_updated_at_uses_earlier_equal_subject() -> None:
    tasks = [
        _task("t-earlier", "ship", "superseded", 2, effort="gamma"),
        _task("t-later", "ship", "done", 3),
    ]
    checks = [_check("c1", "ship-run", 12, effort="gamma")]
    assert _updated(tasks, checks) == _naive(tasks, checks)
    assert _updated(tasks, checks) == datetime.fromisoformat(_at(12))


def test_phase_updated_at_scales_with_one_owner_lookup() -> None:
    tasks = [_task(f"t-{index}", f"task-{index}", "done", 1) for index in range(400)]
    tasks.append(_task("t-old", "task-0-old", "superseded", 2))
    checks = [
        _check(f"c-{index}-{copy}", f"task-{index}-run-{copy}", 3)
        for index in range(400)
        for copy in range(5)
    ]
    started = time.perf_counter()
    found = _updated(tasks, checks)
    elapsed = time.perf_counter() - started
    assert found == datetime.fromisoformat(_at(3))
    assert elapsed < 0.5
