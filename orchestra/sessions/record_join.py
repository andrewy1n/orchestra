from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import overload

from orchestra.sessions.types import (
    RecordJoinBucket,
    RecordJoinResult,
    RecordMetadata,
    SessionFields,
)


@overload
def _parse(value: datetime | str) -> datetime: ...


@overload
def _parse(value: None) -> None: ...


def _parse(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def _window(session: SessionFields) -> tuple[datetime, datetime] | None:
    start, end = _parse(session.get("start")), _parse(session.get("end"))
    if start is None or end is None:
        return None
    return start, end


def join(sessions: list[SessionFields], records: list[RecordMetadata]) -> RecordJoinResult:
    by_session: dict[str, RecordJoinBucket] = {
        s["session_id"]: {"records": [], "ambiguous": []}
        for s in sessions
        if isinstance(s["session_id"], str)
    }
    windows: list[tuple[str, str, tuple[datetime, datetime] | None]] = []
    for session in sessions:
        session_id = session["session_id"]
        if not isinstance(session_id, str):
            continue
        cwd = session.get("cwd")
        name = PurePosixPath(cwd if isinstance(cwd, str) else "").name
        windows.append((session_id, name, _window(session)))
    unattached: list[str] = []
    for rec in records:
        when = _parse(rec["recorded_at"])
        hits = [
            sid
            for sid, name, win in windows
            if win and name == rec["store"] and win[0] <= when <= win[1]
        ]
        for sid in hits:
            by_session[sid]["records"].append(rec["id"])
            if len(hits) > 1:
                by_session[sid]["ambiguous"].append(rec["id"])
        if not hits:
            unattached.append(rec["id"])
    return {"by_session": by_session, "unattached": unattached}
