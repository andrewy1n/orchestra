from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from test_execution_cost_landing import START, _evidence_file, _report, _world

from orchestra.conductor import land_task


def test_r8_duplicate_landing_reuses_report_when_elapsed_time_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo, _ = _world(
        tmp_path, dispatch_id="dispatch-1", dispatched_at=START.isoformat()
    )
    receipts = iter((START + timedelta(seconds=10), START + timedelta(seconds=30)))
    monkeypatch.setattr(land_task, "utc_now", lambda: next(receipts))
    evidence = _evidence_file(tmp_path, tokens_total=123)

    first = land_task.land(project, repo, "cost-task", evidence)
    monkeypatch.setattr(
        land_task,
        "landing_cost_fields",
        lambda *_args: {
            "dispatch_id": "dispatch-1",
            "duration_s": 30,
            "tokens_total": 123,
        },
    )
    second = land_task.land(project, repo, "cost-task", evidence)

    assert second.report_id == first.report_id
    assert _report(project, second.report_id)["duration_s"] == 10
    assert _report(project, second.report_id)["tokens_total"] == 123


def test_r8_new_dispatch_identity_creates_a_new_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project, repo, _ = _world(
        tmp_path, dispatch_id="dispatch-1", dispatched_at=START.isoformat()
    )
    receipts = iter((START + timedelta(seconds=10), START + timedelta(seconds=30)))
    monkeypatch.setattr(land_task, "utc_now", lambda: next(receipts))
    evidence = _evidence_file(tmp_path, tokens_total=123)

    first = land_task.land(project, repo, "cost-task", evidence)
    item = project.resolve("score:work-item", "cost-task")
    project.update(
        item["id"],
        record_type="score:work-item",
        payload={
            "dispatch_id": "dispatch-2",
            "dispatched_at": (START + timedelta(seconds=20)).isoformat(),
        },
    )
    second = land_task.land(project, repo, "cost-task", evidence)

    assert second.report_id != first.report_id
    assert _report(project, second.report_id)["dispatch_id"] == "dispatch-2"


def test_r8_legacy_landing_reuses_report_without_dispatch_identity(tmp_path: Path) -> None:
    project, repo, _ = _world(tmp_path)
    evidence = _evidence_file(tmp_path)

    first = land_task.land(project, repo, "cost-task", evidence)
    second = land_task.land(project, repo, "cost-task", evidence)

    assert second.report_id == first.report_id
    assert "dispatch_id" not in _report(project, second.report_id)
    assert "duration_s" not in _report(project, second.report_id)
