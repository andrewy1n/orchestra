"""Head evidence rules for Conductor check-runs.

One implementation of ownership, correction, latest-order and revision rules
for the acceptance, review and suite questions a caller asks of a phase head.
The module reads no store, Git state or file. Callers pass the records and
select the head.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from heapq import merge

from orchestra.canon.types import Record
from orchestra.conductor.revision import revision_matches
from orchestra.score.lookups import check_run_criteria, corrected_ids, record_order
from orchestra.tuner.records import CheckRun, read_check_run

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
    """Check-run lookups for one unchanged record snapshot."""

    def __init__(self, records: Sequence[Record]) -> None:
        corrected = corrected_ids(records)
        self.check_runs: list[Record] = [
            record
            for record in records
            if record["record_type"] == CHECK_RUN_TYPE and record["id"] not in corrected
        ]
        self._by_criterion: dict[str, list[tuple[int, Record]]] = {}
        for position, run in enumerate(self.check_runs):
            self._by_criterion.setdefault(_text(run, "criterion_id"), []).append((position, run))
        self._typed: dict[str, CheckRun] = {}

    def check_run(self, record: Record) -> CheckRun:
        typed = self._typed.get(record["id"])
        if typed is None:
            write_order = record.get("derived", {}).get("write_order", 0)
            typed = self._typed[record["id"]] = read_check_run(record, write_order)
        return typed

    def acceptance_runs(self, acceptance: Record) -> list[Record]:
        groups = [self._by_criterion.get(name, []) for name in check_run_criteria(acceptance)]
        return [run for _, run in merge(*groups, key=lambda item: item[0])]


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
    if not runs:
        return None
    return max(runs, key=record_order)


def _at_head(runs: Sequence[Record], head: str | None) -> list[Record]:
    if head is None:
        return list(runs)
    return [run for run in runs if revision_matches(_text(run, "revision"), head)]


def acceptance_runs(index: EvidenceIndex, acceptance: Record) -> list[Record]:
    return index.acceptance_runs(acceptance)


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
    candidates = _at_head(acceptance_runs(index, acceptance), head)
    return _decide(latest(candidates), "check-run", head)


def acceptance_runner_at_head(index: EvidenceIndex, acceptance: Record, head: str | None) -> Answer:
    candidates = _at_head(acceptance_runs(index, acceptance), head)
    passing = [
        run
        for run in candidates
        if _text(run, "runner") == RUNNER and _text(run, "result") == "pass"
    ]
    deciding = latest(passing)
    if deciding is None:
        return Answer(False, None, f"no passing runner check-run {_where(head)}")
    return Answer(True, deciding)


def review_check_runs(index: EvidenceIndex, phase_slug: str, effort: str) -> list[Record]:
    subject = phase_slug + REVIEW_SUBJECT_SUFFIX
    return [
        run
        for run in index.check_runs
        if _text(run, "method") == REVIEW_METHOD
        and _text(run, "effort") == effort
        and _names(run, subject)
    ]


def latest_review(index: EvidenceIndex, phase_slug: str, effort: str) -> Record | None:
    return latest(review_check_runs(index, phase_slug, effort))


def review_at_head(index: EvidenceIndex, phase_slug: str, effort: str, head: str | None) -> Answer:
    candidates = _at_head(review_check_runs(index, phase_slug, effort), head)
    return _decide(latest(candidates), "review check-run", head)


def suite_check_runs(index: EvidenceIndex, phase_slug: str) -> list[Record]:
    subject = suite_subject(phase_slug)
    return [
        run
        for run in index.check_runs
        if _text(run, "evidence_kind") == SUITE_EVIDENCE_KIND and _names(run, subject)
    ]


def suite_at_head(index: EvidenceIndex, phase_slug: str, head: str | None) -> Answer:
    candidates = _at_head(suite_check_runs(index, phase_slug), head)
    passing = [run for run in candidates if _text(run, "result") == "pass"]
    deciding = latest(passing)
    if deciding is not None:
        return Answer(True, deciding)
    reason = f"no passing {suite_subject(phase_slug)} {_where(head)}"
    return Answer(False, latest(candidates), reason)
