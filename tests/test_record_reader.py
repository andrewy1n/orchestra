from datetime import datetime, timezone
from pathlib import Path

import pytest

from orchestra.canon import record
from orchestra.canon.project import open_store
from orchestra.sessions.record_reader import RecordReadError, read_project_records


def test_production_reader_returns_only_session_metadata(
    store: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = open_store(store)
    monkeypatch.setattr(record, "now", lambda: "2026-09-30T05:30:00-07:00")
    effort = project.create(
        record_type="score:effort",
        subject="reader",
        payload={"goal": "private goal", "kind": "repair"},
        body="private body",
    )
    phase = project.create(
        record_type="score:phase",
        subject="review-reader",
        payload={"effort": "reader", "title": "private title", "ordinal": 1},
        body="## Problem\nOne\n## Approach\nTwo\n## Exit criteria\nThree",
    )
    token = project.change_token()
    assert read_project_records(project, ["score:phase"]) == [
        {
            "id": phase["id"],
            "record_type": "score:phase",
            "subject": "review-reader",
            "effort": "reader",
            "recorded_at": datetime(2026, 9, 30, 12, 30, tzinfo=timezone.utc),
            "lifecycle_state": "planned",
            "store": str(project.store_path),
        }
    ]
    assert {row["id"]: row["effort"] for row in read_project_records(project)} == {
        effort["id"]: None,
        phase["id"]: "reader",
    }
    assert project.change_token() == token


def test_production_reader_reports_the_unreadable_type(store: Path) -> None:
    project = open_store(store)
    with pytest.raises(RecordReadError, match="absent:kind"):
        read_project_records(project, ["absent:kind"])


def test_production_reader_error_omits_private_content(store: Path) -> None:
    project = open_store(store)
    (project.store_path / "config.json").write_text('{"format": "private-format"}')
    with pytest.raises(RecordReadError, match="score:phase") as failure:
        read_project_records(project, ["score:phase"])
    assert "private-format" not in str(failure.value)
