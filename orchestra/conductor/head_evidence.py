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
from orchestra.conductor.acceptance_amendment import COMMAND_AMENDMENT_KEY
from orchestra.conductor.revision import revision_matches
from orchestra.score.lookups import (
    cached_object,
    check_run_criteria,
    same_prepared_source,
)

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


@dataclass
class _EvidenceParts:
    check_runs: list[Record]
    amended_commands: set[str]
    by_criterion: dict[str, list[tuple[int, Record]]]


def _evidence_parts(records: Sequence[Record]) -> _EvidenceParts:
    corrected = {
        target
        for record in records
        for target in (record.get("relationships") or {}).get("corrects") or []
    }
    check_runs: list[Record] = []
    by_criterion: dict[str, list[tuple[int, Record]]] = {}
    amended: set[str] = set()
    for record in records:
        if record["record_type"] == CHECK_RUN_TYPE:
            if record["id"] in corrected:
                continue
            position = len(check_runs)
            check_runs.append(record)
            by_criterion.setdefault(_text(record, "criterion_id"), []).append((position, record))
            continue
        if record["record_type"] != "conductor:assignment-amendment":
            continue
        provenance = record.get("provenance")
        if isinstance(provenance, dict) and isinstance(
            acceptance_id := provenance.get(COMMAND_AMENDMENT_KEY), str
        ):
            amended.add(acceptance_id)
    return _EvidenceParts(check_runs, amended, by_criterion)


class EvidenceIndex:
    """Check-run lookups for one unchanged record snapshot."""

    def __init__(self, records: Sequence[Record]) -> None:
        if same_prepared_source(records):
            shared = cached_object(records, "evidence-index", lambda: _evidence_parts(records))
            if not isinstance(shared, _EvidenceParts):
                raise TypeError(
                    f"evidence-index cache holds {type(shared).__name__}, expected _EvidenceParts"
                )
        else:
            shared = _evidence_parts(records)
        self.check_runs = shared.check_runs
        self._amended_commands = shared.amended_commands
        self._by_criterion = shared.by_criterion

    def acceptance_runs(self, acceptance: Record) -> list[Record]:
        groups = [self._by_criterion.get(name, []) for name in check_run_criteria(acceptance)]
        require_revision = self.command_was_amended(acceptance)
        runs: list[Record] = []
        for _, run in merge(*groups, key=lambda item: item[0]):
            provenance = run.get("provenance")
            if isinstance(provenance, dict) and "acceptance_revision" in provenance:
                if provenance["acceptance_revision"] == acceptance["revision"]:
                    runs.append(run)
            elif not require_revision:
                runs.append(run)
        return runs

    def command_was_amended(self, acceptance: Record) -> bool:
        return acceptance["id"] in self._amended_commands

    def suite_runs_by_name(self) -> dict[str, list[Record]]:
        """Suite runs keyed by subject and by criterion id."""
        grouped: dict[str, list[Record]] = {}
        for run in self.check_runs:
            if _text(run, "evidence_kind") != SUITE_EVIDENCE_KIND:
                continue
            names = {run["subject"]}
            criterion = _text(run, "criterion_id")
            if criterion:
                names.add(criterion)
            for name in names:
                if name:
                    grouped.setdefault(name, []).append(run)
        return grouped


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
    return max(runs, key=lambda run: (run.get("recorded_at", ""), run["id"]))


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
    what = (
        "check-run for the current acceptance revision"
        if index.command_was_amended(acceptance)
        else "check-run"
    )
    return _decide(latest(candidates), what, head)


def acceptance_runner_at_head(index: EvidenceIndex, acceptance: Record, head: str | None) -> Answer:
    candidates = _at_head(acceptance_runs(index, acceptance), head)
    passing = [
        run
        for run in candidates
        if _text(run, "runner") == RUNNER and _text(run, "result") == "pass"
    ]
    deciding = latest(passing)
    if deciding is None:
        revision = (
            " for the current acceptance revision" if index.command_was_amended(acceptance) else ""
        )
        return Answer(False, None, f"no passing runner check-run{revision} {_where(head)}")
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
    return index.suite_runs_by_name().get(suite_subject(phase_slug), []).copy()


def suite_at_head(index: EvidenceIndex, phase_slug: str, head: str | None) -> Answer:
    candidates = _at_head(suite_check_runs(index, phase_slug), head)
    passing = [run for run in candidates if _text(run, "result") == "pass"]
    deciding = latest(passing)
    if deciding is not None:
        return Answer(True, deciding)
    reason = f"no passing {suite_subject(phase_slug)} {_where(head)}"
    return Answer(False, latest(candidates), reason)
