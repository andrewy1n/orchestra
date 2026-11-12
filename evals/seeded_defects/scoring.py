from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from evals.seeded_defects.cases import DEFECT_KINDS, Case
from evals.seeded_defects.outcomes import Complete, Outcome
from orchestra.conductor.reviewer import ReviewerFinding


@dataclass(frozen=True)
class Score:
    verdict_catch: bool = False
    located_catch: bool = False
    false_alarm: bool = False
    incomplete: bool = False


def _names(text: str, name: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text) is not None


def _finding_text(finding: ReviewerFinding) -> str:
    return "\n".join(str(value) for value in finding.values() if isinstance(value, str))


def _located(case: Case, findings: list[ReviewerFinding]) -> bool:
    names = {
        *case.expected_requirement_ids,
        *case.expected_files,
        *(PurePosixPath(path).name for path in case.expected_files),
    }
    return any(
        _names(_finding_text(finding), name)
        for finding in findings
        if finding.get("blocking")
        for name in names
    )


def score_call(case: Case, outcome: Outcome) -> Score:
    if not isinstance(outcome, Complete):
        return Score(incomplete=True)
    parsed = outcome.parsed
    needs_work = parsed["verdict"] == "NEEDS_WORK"
    is_defect = case.kind in DEFECT_KINDS
    return Score(
        verdict_catch=needs_work and is_defect,
        located_catch=is_defect and _located(case, parsed["findings"]),
        false_alarm=needs_work and not is_defect,
    )
