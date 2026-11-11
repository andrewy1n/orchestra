from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.project import open_store
from orchestra.tools.git import Git

REPAIR_LINK = "conductor:repair-link"
FIELD_SEP = "\x1f"
RECORD_SEP = "\x1e"


@dataclass(frozen=True)
class RepairRow:
    sha: str
    subject: str
    committed_at: str
    cause: str | None
    phase: str | None


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _instant(value: str) -> datetime:
    moment = datetime.fromisoformat(value)
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def build_repair_rows(directory: Path, *, since: str) -> list[RepairRow]:
    log = Git(directory).text(
        "log",
        "main",
        f"--format=%H{FIELD_SEP}%cI{FIELD_SEP}%s{RECORD_SEP}",
    )
    start = _instant(since)
    links: dict[str, tuple[str | None, str | None]] = {}
    for record in open_store(directory, read_only=True).records():
        if record["record_type"] != REPAIR_LINK:
            continue
        payload = record_payload(record)
        sha = _text(payload.get("fix"))
        if sha is not None:
            links[sha] = (_text(payload.get("cause")), _text(payload.get("phase")))
    rows: list[RepairRow] = []
    for entry in log.split(RECORD_SEP):
        entry = entry.strip()
        if not entry:
            continue
        sha, committed_at, subject = entry.split(FIELD_SEP, 2)
        if not subject.startswith("fix") or _instant(committed_at) < start:
            continue
        cause, phase = links.get(sha, (None, None))
        rows.append(RepairRow(sha, subject, committed_at, cause, phase))
    return rows
