from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest
from dashboard_seed_support import seed_project
from fastapi.testclient import TestClient

from dashboard.backend import store
from dashboard.backend.approval import evidence_panels
from dashboard.backend.server.app import create_app
from dashboard.backend.snapshot import NeedsYouItem
from dashboard.backend.task import load_task_detail
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.tuner.record_facts import RecordShapeError

BAD_ID = "<cr:malformed>"


@pytest.fixture()
def project(tmp_path: Path) -> Project:
    return seed_project(tmp_path)


def _check_run(subject: str, drop: str) -> Record:
    payload: JsonObject = {
        "criterion_id": "<acc:1>",
        "revision": "abcdef0123",
        "result": "pass",
        "method": "manual",
        "signed_by": "",
        "effort": "e",
    }
    del payload[drop]
    return {
        "id": BAD_ID,
        "record_type": "tuner:check-run",
        "subject": subject,
        "payload": payload,
        "lifecycle_state": "recorded",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00Z",
    }


def _finding(drop: str) -> Record:
    payload: JsonObject = {"claim": "c", "basis": "b", "needs": "human", "effort": "e"}
    del payload[drop]
    return {
        "id": "<f:malformed>",
        "record_type": "tuner:finding",
        "subject": "f",
        "payload": payload,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "r1",
        "recorded_at": "2026-11-01T00:00:00Z",
    }


def _inject_into_subject_listing(monkeypatch: pytest.MonkeyPatch, extra: Record) -> None:
    real = store.list_records

    def listing(
        target: Project,
        record_type: str | None = None,
        *,
        state: str | None = None,
        subject: str | None = None,
        payload: Mapping[str, str] | None = None,
    ) -> list[Record]:
        rows = real(target, record_type, state=state, subject=subject, payload=payload)
        if subject and record_type is None:
            return [*rows, {**extra, "subject": subject}]
        return rows

    monkeypatch.setattr(store, "list_records", listing)


@pytest.mark.parametrize("field", ["criterion_id", "revision", "result", "method", "signed_by"])
def test_task_detail_http_reports_a_malformed_check_run_as_an_error_body(
    project: Project, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    task = project.list("score:work-item")[0]
    _inject_into_subject_listing(monkeypatch, _check_run(task["subject"], field))
    client = TestClient(create_app(project), raise_server_exceptions=False)
    response = client.get(f"/api/task?id={task['id']}")
    assert response.status_code == 404, response.text
    assert BAD_ID in response.json()["error"]
    assert field in response.json()["error"]


def test_load_task_detail_raises_record_shape_error_for_a_malformed_check_run(
    project: Project, monkeypatch: pytest.MonkeyPatch
) -> None:
    task = project.list("score:work-item")[0]
    _inject_into_subject_listing(monkeypatch, _check_run(task["subject"], "criterion_id"))
    with pytest.raises(RecordShapeError, match="criterion_id"):
        load_task_detail(project, task["id"])


def test_task_detail_http_still_serves_a_store_without_malformed_records(
    project: Project,
) -> None:
    task = project.list("score:work-item")[0]
    client = TestClient(create_app(project), raise_server_exceptions=False)
    assert client.get(f"/api/task?id={task['id']}").status_code == 200


def _needs_item(record: Record) -> NeedsYouItem:
    kind = "unsigned-check" if record["record_type"] == "tuner:check-run" else "needs-human"
    return NeedsYouItem(
        kind=kind,
        id=record["id"],
        subject=record["subject"],
        text="item",
        record_type=record["record_type"],
    )


@pytest.mark.parametrize("field", ["revision", "criterion_id"])
def test_approval_evidence_reports_a_malformed_check_run(
    project: Project, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    record = _check_run("s", field)
    monkeypatch.setattr(store, "stored_record", lambda *_args, **_kwargs: record)
    with pytest.raises(RecordShapeError) as caught:
        evidence_panels(project, _needs_item(record), root=tmp_path, view=None)
    assert BAD_ID in str(caught.value)
    assert field in str(caught.value)


@pytest.mark.parametrize("field", ["claim", "basis"])
def test_approval_evidence_reports_a_malformed_finding(
    project: Project, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    record = _finding(field)
    monkeypatch.setattr(store, "stored_record", lambda *_args, **_kwargs: record)
    with pytest.raises(RecordShapeError) as caught:
        evidence_panels(project, _needs_item(record), root=tmp_path, view=None)
    assert "<f:malformed>" in str(caught.value)
    assert field in str(caught.value)
