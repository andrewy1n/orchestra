import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from orchestra.canon import record
from orchestra.canon.errors import StoreError
from orchestra.canon.project import open_store
from orchestra.sessions import session_report

SCRIPT = Path(__file__).resolve().parent.parent / "orchestra" / "sessions" / "session_report.py"


def write(path, events, extra=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in events) + extra)


def build(root):
    write(
        root / "projA" / "s1.jsonl",
        [
            {
                "type": "user",
                "sessionId": "s1",
                "timestamp": "2026-01-01T00:00:00Z",
                "message": {"role": "user", "content": "SECRET prompt"},
            },
            {
                "type": "assistant",
                "timestamp": "2026-01-01T00:01:00Z",
                "message": {
                    "content": [
                        {"type": "tool_use", "id": "1", "name": "Bash", "input": {"cmd": "SECRET"}}
                    ]
                },
            },
            {
                "type": "user",
                "timestamp": "2026-01-01T00:01:05Z",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "1",
                            "content": "SECRET",
                            "is_error": True,
                        }
                    ]
                },
            },
        ],
        extra="not json\n",
    )
    write(root / "projA" / "s2.jsonl", [{"type": "user", "sessionId": "s2"}])
    write(root / "projB" / "s3.jsonl", [{"type": "user", "sessionId": "s3"}])
    write(root / "projB" / "s3" / "subagents" / "agent.jsonl", [{"type": "user"}])
    (root / "projB" / "notes.txt").write_text("x")


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True
    )


def test_prints_one_json_summary_per_top_level_session(tmp_path):
    build(tmp_path)
    proc = run(tmp_path)
    assert proc.returncode == 0
    rows = [json.loads(line) for line in proc.stdout.splitlines()]
    assert sorted(r["file"] for r in rows) == ["s1.jsonl", "s2.jsonl", "s3.jsonl"]
    s1 = next(r for r in rows if r["file"] == "s1.jsonl")
    assert s1["project"] == "projA"
    assert s1["session_id"] == "s1"
    assert s1["turns"] == 1
    assert s1["bad_lines"] == 1
    assert s1["tools"]["tools"]["Bash"]["errors"] == 1


def test_output_holds_no_message_text(tmp_path):
    build(tmp_path)
    assert "SECRET" not in run(tmp_path).stdout


def test_unreadable_file_reports_error_class_and_run_continues(tmp_path):
    build(tmp_path)
    (tmp_path / "projA" / "bad.jsonl").mkdir()
    proc = run(tmp_path)
    assert proc.returncode == 0
    rows = [json.loads(line) for line in proc.stdout.splitlines()]
    bad = next(r for r in rows if r["file"] == "bad.jsonl")
    assert bad["error"] == "IsADirectoryError"
    assert len(rows) == 4


def test_missing_projects_dir_prints_nothing_and_exits_zero(tmp_path):
    proc = run(tmp_path / "nope")
    assert proc.returncode == 0
    assert proc.stdout == ""


def build_records(root, cwd):
    write(
        root / "projA" / "s1.jsonl",
        [
            {
                "type": "user",
                "sessionId": "s1",
                "cwd": str(cwd),
                "timestamp": "2026-01-01T00:00:00Z",
            },
            {"type": "user", "timestamp": "2026-01-01T01:00:00Z"},
        ],
    )
    write(
        root / "projA" / "s2.jsonl",
        [
            {
                "type": "user",
                "sessionId": "s2",
                "cwd": str(cwd),
                "timestamp": "2026-01-01T00:30:00Z",
            },
            {"type": "user", "timestamp": "2026-01-01T02:00:00Z"},
        ],
    )
    write(
        root / "projB" / "s3.jsonl",
        [
            {
                "type": "user",
                "sessionId": "s3",
                "cwd": "/nowhere/nostore",
                "timestamp": "2026-01-01T00:00:00Z",
            },
            {"type": "user", "timestamp": "2026-01-01T01:00:00Z"},
        ],
    )


@pytest.fixture
def records_report(store: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CANON_STORE", raising=False)
    project = open_store(store)
    for effort in ("eff-a", "eff-b"):
        project.create(
            record_type="score:effort", subject=effort, payload={"goal": effort, "kind": "repair"}
        )
    project.create(
        record_type="score:phase",
        subject="phase",
        payload={"title": "Phase", "ordinal": 1, "effort": "eff-a"},
        body="## Problem\nA\n## Approach\nB\n## Exit criteria\nC",
    )
    for minute, task, effort in (("10", "task-one", "eff-a"), ("40", "task-two", "eff-b")):
        timestamp = f"2026-01-01T00:{minute}:00Z"
        monkeypatch.setattr(record, "now", lambda timestamp=timestamp: timestamp)
        project.create(
            record_type="score:work-item",
            subject=task,
            payload={
                "title": task,
                "phase": "phase",
                "effort": effort,
                "assignee": "",
                "kind": "repair",
            },
            body="## Description\nSECRET",
        )
    monkeypatch.setattr(record, "now", lambda: "2026-01-01T01:30:00Z")
    project.create(
        record_type="tuner:finding",
        subject="SECRET-subject",
        payload={
            "claim": "SECRET",
            "basis": "temporary",
            "invalidated_when": "later",
            "needs": "none",
            "effort": "eff-a",
        },
        body="## Evidence\nSECRET\n## Consequence\nA\n## Follow-up\nB",
    )
    build_records(tmp_path / "projects", store)
    result = run("--records", tmp_path / "projects")
    assert result.returncode == 0, result.stderr
    return result.stdout


def parse(out):
    return {json.loads(line)["file"]: json.loads(line) for line in out.splitlines()}


def test_records_flag_adds_per_session_counts_by_type(records_report: str) -> None:
    rows = parse(records_report)
    s1 = rows["s1.jsonl"]["records"]
    assert s1 == {
        "total": 2,
        "by_type": {"score:work-item": 2},
        "efforts": ["eff-a", "eff-b"],
        "tasks": ["task-one", "task-two"],
        "ambiguous": 1,
    }
    s2 = rows["s2.jsonl"]["records"]
    assert s2["total"] == 2
    assert s2["by_type"] == {"score:work-item": 1, "tuner:finding": 1}
    assert s2["tasks"] == ["task-two"]
    assert s2["ambiguous"] == 1


def test_session_without_matches_gets_zero_and_empty_collections(records_report: str) -> None:
    rows = parse(records_report)
    assert rows["s3.jsonl"]["records"] == {
        "total": 0,
        "by_type": {},
        "efforts": [],
        "tasks": [],
        "ambiguous": 0,
    }


def test_records_output_holds_no_record_text_or_ids(records_report: str) -> None:
    assert "SECRET" not in records_report
    assert "rec-" not in records_report


def test_without_flag_output_is_unchanged_and_reader_is_not_called(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    build(tmp_path)

    def boom(argv: str) -> None:
        raise AssertionError("reader called")

    monkeypatch.setattr(session_report, "open_store", boom)
    session_report.main([str(tmp_path)])
    out = capsys.readouterr().out
    assert out == run(tmp_path).stdout
    assert all("records" not in json.loads(line) for line in out.splitlines())


def test_records_read_failure_keeps_rows_and_returns_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    good_cwd = tmp_path / "good"
    bad_cwd = tmp_path / "bad"
    transcripts = tmp_path / "logs"
    write(
        transcripts / "project" / "good.jsonl",
        [{"type": "user", "cwd": str(good_cwd), "sessionId": "good"}],
    )
    write(
        transcripts / "project" / "bad.jsonl",
        [{"type": "user", "cwd": str(bad_cwd), "sessionId": "bad"}],
    )

    class _Project:
        def __init__(self, cwd: Path) -> None:
            self.store_path = cwd

        def list(self, record_type: str):
            if self.store_path == bad_cwd:
                raise StoreError("store read failed")
            return []

    monkeypatch.setattr(session_report, "open_store", lambda cwd: _Project(Path(cwd)))

    result = session_report.main(["--records", str(transcripts)])

    captured = capsys.readouterr()
    rows = [json.loads(line) for line in captured.out.splitlines()]
    assert result == 2
    assert {row["session_id"] for row in rows} == {"good", "bad"}
    assert "RecordReadError" in captured.err
    assert "records" not in next(row for row in rows if row["session_id"] == "bad")


def _report_count(transcripts: Path, cwd: Path) -> dict[str, int]:
    write(
        transcripts / "project" / "bound.jsonl",
        [
            {
                "type": "user",
                "cwd": str(cwd),
                "sessionId": "bound",
                "timestamp": "2000-01-01T00:00:00Z",
            },
            {"type": "user", "timestamp": "2099-12-31T23:59:59Z"},
        ],
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "orchestra.cli",
            "sessions",
            "report",
            str(transcripts),
            "--records",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)["records"]["by_type"]


def test_local_binding(tmp_path: Path, store: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CANON_STORE", raising=False)
    (store / ".canon" / "store-binding.json").write_text('{"store":"local"}')
    open_store(store).create(
        record_type="score:effort", subject="local", payload={"goal": "local", "kind": "repair"}
    )
    nested = store / "src"
    nested.mkdir()
    assert _report_count(tmp_path / "logs", nested) == {"score:effort": 1}


def test_store_override(tmp_path: Path, store: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CANON_STORE", raising=False)
    override = tmp_path / "override"
    shutil.copytree(store / ".canon", override)
    open_store(store).create(
        record_type="score:effort", subject="local", payload={"goal": "local", "kind": "repair"}
    )
    monkeypatch.setenv("CANON_STORE", str(override))
    for subject in ("first", "second"):
        open_store(store).create(
            record_type="score:effort", subject=subject, payload={"goal": subject, "kind": "repair"}
        )
    assert _report_count(tmp_path / "logs", store) == {"score:effort": 2}
