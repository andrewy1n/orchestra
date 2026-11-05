"""Read record metadata through the artifact library, never bodies."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.derive import WORK_ITEM, task_assignment
from orchestra.sessions.session_types import RecordMetadata

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


def _utc(ts: str) -> datetime:
    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _metadata(raw: Record, store: str, siblings: list[Record]) -> RecordMetadata:
    payload = raw.get("payload", {})
    effort = payload.get("effort")
    row: RecordMetadata = {
        "id": raw["id"],
        "record_type": raw["record_type"],
        "subject": raw.get("subject"),
        "effort": effort if isinstance(effort, str) else None,
        "recorded_at": _utc(raw["recorded_at"]),
        "lifecycle_state": raw.get("lifecycle_state"),
        "store": store,
    }
    if raw["record_type"] == WORK_ITEM:
        assignment = task_assignment(raw, siblings)
        if assignment is not None and assignment.assignee:
            row["assignee"] = assignment.assignee
        if assignment is not None and assignment.write_root:
            row["write_root"] = assignment.write_root
    return row


def _metadata_rows(raws: list[Record], store: str) -> list[RecordMetadata]:
    try:
        return [_metadata(raw, store, raws) for raw in raws]
    except (KeyError, TypeError, ValueError) as exc:
        raise RecordReadError(f"cannot read records ({type(exc).__name__})") from None


def read_project_records(
    project: Project, types: Iterable[str] | None = None
) -> list[RecordMetadata]:
    raws: list[Record] = []
    chosen = types if types is not None else DEFAULT_TYPES
    for record_type in chosen:
        try:
            raws.extend(project.list(record_type))
        except (StoreError, OSError, KeyError, TypeError, ValueError) as exc:
            raise RecordReadError(
                f"cannot read records of type {record_type} ({type(exc).__name__})"
            ) from None
    return _metadata_rows(raws, str(project.store_path))
