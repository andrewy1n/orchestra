from __future__ import annotations

from collections.abc import Sequence

from orchestra.canon.types import Record
from orchestra.conductor.head_evidence import SUITE_EVIDENCE_KIND, EvidenceIndex, suite_subject
from orchestra.score.lookups import latest_record
from orchestra.tuner.evidence.record_facts import check_run_facts

LEGACY_TIER2_SUBJECT_SUFFIX = "-tier2"
SUITE_RUNNING_MARKER = "suite-running"
LEGACY_TIER2_RUNNING_MARKER = "tier2-running"
_INACTIVE = ("superseded", "retracted")


def _short_revision(revision: str) -> str:
    rev = revision.strip()
    return rev[:7] if rev else "?"


def _label(record: Record) -> str:
    facts = check_run_facts(record)
    body = record.get("body") or ""
    if facts.result == "blocked" and (
        SUITE_RUNNING_MARKER in body or LEGACY_TIER2_RUNNING_MARKER in body
    ):
        return "suite running"
    short = _short_revision(facts.revision)
    if facts.result == "pass":
        return f"suite ok@{short}"
    if facts.result == "fail":
        return f"suite fail@{short}"
    return ""


class SuiteLabels:
    def __init__(self, checks: Sequence[Record]) -> None:
        self._primary = {
            name: [run for run in runs if run.get("lifecycle_state") not in _INACTIVE]
            for name, runs in EvidenceIndex(checks).suite_runs_by_name().items()
        }
        self._legacy: dict[str, list[Record]] = {}
        for run in checks:
            if run.get("lifecycle_state") in _INACTIVE:
                continue
            subject = run.get("subject") or ""
            if not subject.endswith(LEGACY_TIER2_SUBJECT_SUFFIX):
                continue
            if check_run_facts(run).evidence_kind != SUITE_EVIDENCE_KIND:
                continue
            self._legacy.setdefault(subject, []).append(run)

    def label(self, phase: str) -> str:
        record = latest_record(self._primary.get(suite_subject(phase), []))
        if record is None:
            record = latest_record(self._legacy.get(f"{phase}{LEGACY_TIER2_SUBJECT_SUFFIX}", []))
        return "" if record is None else _label(record)


def suite_labels(checks: Sequence[Record]) -> SuiteLabels:
    return SuiteLabels(checks)


def suite_status_label(phase: str, checks: Sequence[Record]) -> str:
    return SuiteLabels(checks).label(phase)
