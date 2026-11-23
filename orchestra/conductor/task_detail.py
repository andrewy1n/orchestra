from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from orchestra.canon import record_payload
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.assignment import failed_attempt
from orchestra.score.facts.detail_facts import DECISION_TYPE
from orchestra.score.facts.work_item_facts import decision_choice
from orchestra.tuner.evidence.evidence_facts import FINDING_TYPE, OBSERVATION_TYPE
from orchestra.tuner.evidence.record_facts import check_run_facts, finding_facts, observation_text

ASSIGNMENT_AMENDMENT_TYPE = "conductor:assignment-amendment"
EXECUTION_REPORT_TYPE = "conductor:execution-report"
FAILED_ATTEMPT_TYPE = "conductor:failed-attempt"

RELATED_KINDS: dict[str, str] = {
    FINDING_TYPE: "finding",
    DECISION_TYPE: "decision",
    FAILED_ATTEMPT_TYPE: "failed-attempt",
    OBSERVATION_TYPE: "observation",
}

_CHECK_OUTCOME = {"pass": "passed", "fail": "failed"}


@dataclass(frozen=True)
class ReportFacts:
    result: str
    verdict: str
    revision: str


@dataclass(frozen=True)
class TimelineEntry:
    kind: str
    record: Record
    summary: str
    revision: str


def _text(payload: JsonObject, key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def assignment_executor(record: Record) -> str:
    return _text(record_payload(record), "executor")


def report_facts(record: Record) -> ReportFacts:
    payload = record_payload(record)
    return ReportFacts(
        result=_text(payload, "result"),
        verdict=_text(payload, "verdict"),
        revision=_text(payload, "revision"),
    )


def related_text(record: Record) -> str:
    record_type = record["record_type"]
    if record_type == FINDING_TYPE:
        return finding_facts(record).claim
    if record_type == DECISION_TYPE:
        choice = decision_choice(record)
        return choice if isinstance(choice, str) else ""
    if record_type == FAILED_ATTEMPT_TYPE:
        return failed_attempt(record).attempted_action
    if record_type == OBSERVATION_TYPE:
        return observation_text(record)
    return ""


def timeline_entries(
    assignments: Sequence[Record],
    amendments: Sequence[Record],
    reports: Sequence[Record],
    checks: Sequence[Record],
) -> list[TimelineEntry]:
    entries = [
        TimelineEntry("assignment", record, f"assigned to {assignment_executor(record)}", "")
        for record in assignments
    ]
    entries.extend(TimelineEntry("assignment-amendment", r, "amended", "") for r in amendments)
    for record in reports:
        facts = report_facts(record)
        entries.append(
            TimelineEntry("execution-report", record, f"reported {facts.verdict}", facts.revision)
        )
    for record in checks:
        check = check_run_facts(record)
        outcome = _CHECK_OUTCOME.get(check.result, check.result)
        entries.append(
            TimelineEntry(
                "check-run", record, f"{check.method} check {outcome}".strip(), check.revision
            )
        )
    return entries
