from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from test_execution_cost_dispatch import START as DISPATCH_START
from test_execution_cost_dispatch import _item, _repo
from test_execution_cost_landing import START, _evidence_file, _report, _world

from orchestra.conductor.tasks import execution_cost, land_task, wave


def test_dispatch_started_at_is_recorded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project, repo = _repo(tmp_path)
    _item(project, "task")
    monkeypatch.setattr(execution_cost, "utc_now", lambda: DISPATCH_START)

    wave.start(project, repo, "cost-phase")

    task = project.resolve("score:work-item", "task")
    assert task["payload"]["dispatch_started_at"] == DISPATCH_START.isoformat(
        timespec="microseconds"
    )


def test_same_dispatch_changed_evidence_records_new_duration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo, _ = _world(
        tmp_path, dispatch_id="dispatch-1", dispatch_started_at=START.isoformat()
    )
    receipts = iter((START + timedelta(seconds=10), START + timedelta(seconds=30)))
    monkeypatch.setattr(land_task, "utc_now", lambda: next(receipts))

    first = land_task.land(project, repo, "cost-task", _evidence_file(tmp_path))
    second = land_task.land(
        project,
        repo,
        "cost-task",
        _evidence_file(tmp_path, evidence="Different evidence for the same dispatch."),
    )

    assert second.report_id != first.report_id
    assert _report(project, first.report_id)["duration_s"] == 10
    assert _report(project, second.report_id)["duration_s"] == 30
