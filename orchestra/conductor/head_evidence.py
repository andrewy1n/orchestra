"""Head evidence rules for Conductor check-runs.

One implementation of ownership, correction, latest-order and revision rules
for the acceptance, review and suite questions a caller asks of a phase head.
The module reads no store, Git state or file. Callers pass the records and
select the head.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from orchestra.canon.types import Record
from orchestra.conductor.revision import revision_matches

CHECK_RUN_TYPE = "tuner:check-run"
RUNNER = "orchestra"
SUITE_EVIDENCE_KIND = "integration"
SUITE_SUBJECT_SUFFIX = "-suite"
REVIEW_METHOD = "review"
REVIEW_SUBJECT_SUFFIX = "-review"


@dataclass(frozen=True)
class Answer:
    holds: bool
    run: Record | None = None
    reason: str = ""


class EvidenceIndex:
    """Check-runs of a record list that no record corrects."""

    def __init__(self, records: Sequence[Record]) -> None:
        corrected: set[str] = set()
        for record in records:
            corrected.update((record.get("relationships") or {}).get("corrects") or [])
        self.check_runs: list[Record] = [
            record
            for record in records
            if record["record_type"] == CHECK_RUN_TYPE
        ]


def suite_subject(phase_slug: str) -> str:
    slug = (phase_slug or "").strip()
    if not slug:
        raise ValueError("phase_slug is required")
    if slug.endswith(SUITE_SUBJECT_SUFFIX):
        return slug
    return f"{slug}{SUITE_SUBJECT_SUFFIX}"


def _text(record: Record, key: str) -> str:
    value = record["payload"].get(key)
    return value if isinstance(value, str) else ""


def _names(record: Record, subject: str) -> bool:
    return subject in {_text(record, "criterion_id"), record["subject"]}


def latest(runs: Sequence[Record]) -> Record | None:
    return None



def _at_head(runs: Sequence[Record], head: str | None) -> list[Record]:
    if head is None:
        return list(runs)
    return [run for run in runs if revision_matches(_text(run, "revision"), head)]


def _acceptance_runs(index: EvidenceIndex, acceptance: Record) -> list[Record]:
    keys = {acceptance["id"], acceptance["subject"]}
    return [run for run in index.check_runs if _text(run, "criterion_id") in keys]


def _where(head: str | None) -> str:
    return "at any revision" if head is None else f"at {head or 'unknown head'}"


def _decide(run: Record | None, what: str, head: str | None) -> Answer:
    if run is None:
        return Answer(False, None, f"no {what} {_where(head)}")
    result = _text(run, "result")
    if result == "pass":
        return Answer(True, run)
    return Answer(False, run, f"latest {what} result is {result}")


def acceptance_latest(index: EvidenceIndex, acceptance: Record, head: str | None) -> Answer:
    return Answer(False, None, "stub")



def acceptance_runner_at_head(index: EvidenceIndex, acceptance: Record, head: str | None) -> Answer:
    return Answer(False, None, "stub")



def review_check_runs(index: EvidenceIndex, phase_slug: str, effort: str) -> list[Record]:
    return []



def latest_review(index: EvidenceIndex, phase_slug: str, effort: str) -> Record | None:
    return latest(review_check_runs(index, phase_slug, effort))


def review_at_head(index: EvidenceIndex, phase_slug: str, effort: str, head: str | None) -> Answer:
    return Answer(False, None, "stub")



def suite_check_runs(index: EvidenceIndex, phase_slug: str) -> list[Record]:
    return []



def suite_at_head(index: EvidenceIndex, phase_slug: str, head: str | None) -> Answer:
    return Answer(False, None, "stub")
