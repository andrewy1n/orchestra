"""Print one JSON summary per session transcript: counts and references only."""

from __future__ import annotations

import json
import queue
import sys
import threading
from collections.abc import Iterator, Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import TypeGuard

from orchestra.canon.project import StoreBindingError, open_store
from orchestra.sessions.record_join import join
from orchestra.sessions.record_reader import read_project_records
from orchestra.sessions.session_fields import session_fields
from orchestra.sessions.session_metrics import ReadStats, read_events
from orchestra.sessions.session_tools import tool_metrics
from orchestra.sessions.session_types import (
    RecordMetadata,
    SessionError,
    SessionOutput,
    SessionRecordSummary,
    SessionReport,
    SessionSummary,
    ToolMetrics,
    TranscriptEvent,
)


class _DrainSignal(Enum):
    done = "done"


_DONE = _DrainSignal.done


def _drain(
    q: queue.Queue[TranscriptEvent | _DrainSignal], state: dict[str, bool]
) -> Iterator[TranscriptEvent]:
    while not state["done"]:
        item = q.get()
        if item is _DONE:
            state["done"] = True
            return
        yield item


def summarize(path: Path) -> SessionSummary:
    stats = ReadStats()
    q: queue.Queue[TranscriptEvent | _DrainSignal] = queue.Queue(maxsize=256)
    box: dict[str, ToolMetrics] = {}
    state = {"done": False}

    def worker() -> None:
        try:
            box["tools"] = tool_metrics(_drain(q, state))
        finally:
            for _ in _drain(q, state):
                pass

    thread = threading.Thread(target=worker)
    thread.start()

    def fan_out() -> Iterator[TranscriptEvent]:
        try:
            for event in read_events(path, stats):
                q.put(event)
                yield event
        finally:
            q.put(_DONE)

    try:
        fields = session_fields(fan_out())
    finally:
        thread.join()
    return {**fields, "tools": box["tools"], "bad_lines": stats.bad_lines}


def _read_all(
    rows: Sequence[SessionReport],
) -> tuple[dict[str, str], list[RecordMetadata], list[str]]:
    stores_by_cwd: dict[str, str] = {}
    by_store: dict[str, list[RecordMetadata]] = {}
    failures: list[str] = []
    cwds = {cwd for row in rows if isinstance((cwd := row.get("cwd")), str) and cwd}
    for cwd in sorted(cwds):
        try:
            project = open_store(cwd)
            key = str(project.store_path)
            if key not in by_store:
                by_store[key] = read_project_records(project)
            stores_by_cwd[cwd] = key
        except StoreBindingError as exc:
            if not str(exc).startswith("No artifact store for "):
                failures.append(f"{cwd}: {type(exc).__name__}: {exc}")
            continue
        except Exception as exc:
            failures.append(f"{cwd}: {type(exc).__name__}: {exc}")
            continue
    records = [record for store_records in by_store.values() for record in store_records]
    return stores_by_cwd, records, failures


def _record_summary(
    ids: list[str], by_id: Mapping[str, RecordMetadata], ambiguous: list[str]
) -> SessionRecordSummary:
    matched = [by_id[i] for i in ids]
    by_type: dict[str, int] = {}
    for rec in matched:
        by_type[rec["record_type"]] = by_type.get(rec["record_type"], 0) + 1
    return {
        "total": len(matched),
        "by_type": by_type,
        "efforts": sorted({r["effort"] for r in matched if r["effort"]}),
        "tasks": sorted(
            {
                r["subject"]
                for r in matched
                if r["record_type"] == "score:work-item" and r["subject"]
            }
        ),
        "ambiguous": len(ambiguous),
    }


def _is_session_report(row: SessionOutput) -> TypeGuard[SessionReport]:
    return "session_id" in row


def _attach_records(rows: list[SessionOutput]) -> list[str]:
    sessions = [row for row in rows if _is_session_report(row) and row.get("session_id")]
    stores_by_cwd, records, failures = _read_all(sessions)
    by_store: dict[str, dict[str, RecordMetadata]] = {}
    for rec in records:
        by_store.setdefault(rec["store"], {})[rec["id"]] = rec
    joined = join(sessions, records, stores_by_cwd)["by_session"]
    for row in sessions:
        session_id = row["session_id"]
        if not isinstance(session_id, str):
            continue
        cwd = row.get("cwd")
        by_id = by_store.get(stores_by_cwd.get(cwd, ""), {}) if isinstance(cwd, str) else {}
        hit = joined[session_id]
        row["records"] = _record_summary(hit["records"], by_id, hit["ambiguous"])
    return failures


def main(argv: list[str]) -> int:
    with_records = "--records" in argv
    args = [a for a in argv if a != "--records"]
    root = Path(args[0]) if args else Path.home() / ".claude" / "projects"
    rows: list[SessionOutput] = []
    for path in sorted(root.glob("*/*.jsonl")):
        try:
            summary = summarize(path)
        except Exception as exc:
            error_row: SessionError = {
                "project": path.parent.name,
                "file": path.name,
                "error": type(exc).__name__,
            }
            row: SessionOutput = error_row
        else:
            row = SessionReport(
                project=path.parent.name,
                file=path.name,
                **summary,
            )
        if with_records:
            rows.append(row)
        else:
            print(json.dumps(row), flush=True)
    if with_records:
        failures = _attach_records(rows)
        for row in rows:
            print(json.dumps(row), flush=True)
        if failures:
            print("orchestra sessions report: " + "; ".join(failures), file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
