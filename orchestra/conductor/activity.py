from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone

from orchestra.canon import record_payload
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.assessment_facts import assessment_summary

_CHECK_OUTCOME = {"pass": "passed", "fail": "failed"}


@dataclass(frozen=True)
class ActivityEntry:
    kind: str
    id: str
    subject: str
    recorded_at: datetime
    summary: str
    failed: bool = False


def _text(payload: JsonObject, key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def _recorded_at(record: Record) -> datetime:
    stamp = record.get("recorded_at")
    return datetime.fromisoformat(stamp) if stamp else datetime.min.replace(tzinfo=timezone.utc)


def activity_entries(
    assignments: Sequence[Record],
    reports: Sequence[Record],
    checks: Sequence[Record],
    efforts_by_work_item: Mapping[str, tuple[str, str]],
    since: datetime,
    assessments: Sequence[Record] | None = None,
    integrations: Sequence[Record] | None = None,
    releases: Sequence[Record] | None = None,
    structured: set[tuple[str, str]] | None = None,
) -> dict[str, list[ActivityEntry]]:
    by_effort: dict[str, list[ActivityEntry]] = {}

    def add(
        effort: str | None, kind: str, record: Record, summary: str, failed: bool = False
    ) -> None:
        if effort is not None and _recorded_at(record) >= since:
            by_effort.setdefault(effort, []).append(
                ActivityEntry(
                    kind, record["id"], record["subject"], _recorded_at(record), summary, failed
                )
            )

    def work_item(record: Record) -> tuple[str | None, str]:
        ref = _text(record_payload(record), "work_item")
        effort, subject = efforts_by_work_item.get(ref, (None, ref))
        return effort, subject

    def in_scope(payload: JsonObject) -> bool:
        return (_text(payload, "effort"), _text(payload, "phase")) in (structured or set())

    for record in assignments:
        effort, subject = work_item(record)
        payload = record_payload(record)
        add(
            _text(payload, "effort") or effort,
            "assignment",
            record,
            f"{subject} assigned to {_text(payload, 'executor')}",
        )
    for record in reports:
        effort, subject = work_item(record)
        payload = record_payload(record)
        add(
            effort,
            "execution-report",
            record,
            f"{subject} reported {_text(payload, 'verdict')}",
            "fail" in (payload.get("result"), payload.get("verdict")),
        )
    for record in checks:
        payload = record_payload(record)
        result = _text(payload, "result")
        outcome = _CHECK_OUTCOME.get(result, result)
        method = _text(payload, "method").replace("check", "").strip()
        label = " ".join(part for part in (record["subject"], method, "check", outcome) if part)
        add(_text(payload, "effort") or None, "check-run", record, label, result == "fail")
    assessment_by_id = {record["id"]: record for record in assessments or []}
    for record in assessments or []:
        payload = record_payload(record)
        if not in_scope(payload):
            continue
        summary = assessment_summary(record, assessment_by_id)
        add(
            _text(payload, "effort"),
            "assessment",
            record,
            summary.text,
            summary.failed,
        )
    for record in integrations or []:
        payload = record_payload(record)
        if not in_scope(payload):
            continue
        result = _text(payload, "result")
        add(
            _text(payload, "effort"),
            "integration",
            record,
            f"{_text(payload, 'phase')} {result}",
            result in ("fail", "blocked"),
        )
    for record in releases or []:
        payload = record_payload(record)
        if not in_scope(payload):
            continue
        state = _text(payload, "state")
        add(
            _text(payload, "effort"),
            "release",
            record,
            f"{_text(payload, 'phase')} {state}",
            state == "failed",
        )
    for items in by_effort.values():
        items.sort(key=lambda item: item.recorded_at, reverse=True)
    return by_effort
