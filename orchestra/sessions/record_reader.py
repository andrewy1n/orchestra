"""Read record metadata through the artifact library, never bodies."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable, Iterable
from datetime import datetime, timezone

from orchestra.canon.project import open_store
from orchestra.canon.errors import StoreError

DEFAULT_TYPES = (
    "score:acceptance",
    "score:effort",
    "conductor:assignment",
    "conductor:assignment-amendment",
    "tuner:check-run",
    "score:constraint",
    "score:continuity-question",
    "score:position",
    "score:decision",
    "conductor:execution-report",
    "tuner:finding",
    "tuner:investigation-observation",
    "score:phase",
    "score:work-item",
)


class RecordReadError(RuntimeError):
    pass


def subprocess_runner(argv: list[str]) -> str:
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RecordReadError(f"exit code {proc.returncode}")
    return proc.stdout


def _utc(ts: str) -> datetime:
    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _metadata(raw: dict, store: str) -> dict:
    payload = raw.get("payload") or {}
    return {
        "id": raw["id"],
        "record_type": raw["record_type"],
        "subject": raw.get("subject"),
        "effort": payload.get("effort"),
        "recorded_at": _utc(raw["recorded_at"]),
        "lifecycle_state": raw.get("lifecycle_state"),
        "store": store,
    }


def _read_open_store(root: str, types: Iterable[str] | None) -> list[dict]:
    project = open_store(root)
    rows: list[dict] = []
    chosen = types if types is not None else DEFAULT_TYPES
    for record_type in chosen:
        try:
            records = project.list(record_type)
            rows.extend(_metadata(record, project.project_root.name) for record in records)
        except (StoreError, OSError, KeyError, TypeError, ValueError) as exc:
            raise RecordReadError(
                f"cannot read records of type {record_type} ({type(exc).__name__})"
            ) from None
    return rows


def read_records(
    root: str,
    types: Iterable[str] | None = None,
    run: Callable[[list[str]], str] | None = None,
) -> list[dict]:
    if run is None or run is subprocess_runner:
        return _read_open_store(root, types)
    store = os.path.basename(os.path.abspath(root))
    store_path = os.path.join(os.path.expanduser("~"), ".canon", store)
    rows: list[dict] = []
    for record_type in types if types is not None else DEFAULT_TYPES:
        argv = [
            "record-list",
            "--root",
            root,
            "--store",
            store_path,
            "--read-only",
            "list",
            "--type",
            record_type,
        ]
        try:
            records = json.loads(run(argv))["records"]
            rows.extend(_metadata(record, store) for record in records)
        except Exception as exc:
            raise RecordReadError(
                f"cannot read records of type {record_type} ({type(exc).__name__})"
            ) from None
    return rows
