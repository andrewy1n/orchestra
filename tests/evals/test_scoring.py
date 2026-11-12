from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from evals.seeded_defects.cases import Case
from evals.seeded_defects.outcomes import Complete, Incomplete, IncompleteReason
from evals.seeded_defects.scoring import Score, score_call
from orchestra.conductor.reviewer import ParsedReviewerOutput, ReviewerFinding

INTEGRATION = {"interfaces": "", "assumptions": "", "invariants": "", "conflicts": ""}


def finding(observed: str = "", *, blocking: bool = True, **fields: str) -> ReviewerFinding:
    base: ReviewerFinding = {
        "task": "t",
        "kind": "missing-test",
        "expected": fields.get("expected", ""),
        "observed": observed,
        "severity": "major",
        "blocking": blocking,
    }
    if "requirement" in fields:
        base["requirement"] = fields["requirement"]
    return base


def parsed(*findings: ReviewerFinding) -> Complete:
    output: ParsedReviewerOutput = {
        "verdict": "NEEDS_WORK" if any(f.get("blocking") for f in findings) else "PASS",
        "findings": list(findings),
        "integration": INTEGRATION.copy(),  # pyright: ignore[reportAssignmentType]
        "demoted": [],
    }
    return Complete(output)


def case(kind: str) -> Case:
    return Case(
        id="c1",
        phase="p",
        revision="abc",
        kind=kind,
        defect_type=None if kind == "control" else "removed-test",
        patch=None if kind == "control" else Path("patch.diff"),
        expected_files=frozenset({"orchestra/store/db.py"}),
        expected_requirement_ids=frozenset({"R7"}),
    )


DEFECT = case("synthetic-defect")
ESCAPE = case("real-escape")
CONTROL = case("control")

VERDICT_CATCH_CASES = [
    pytest.param(
        DEFECT, parsed(finding("unrelated text")), True, id="needs-work-on-synthetic-defect"
    ),
    pytest.param(ESCAPE, parsed(finding("unrelated text")), True, id="needs-work-on-real-escape"),
    pytest.param(DEFECT, parsed(), False, id="pass-on-defect-is-a-miss"),
    pytest.param(
        DEFECT, parsed(finding("unrelated", blocking=False)), False, id="advisory-only-is-a-miss"
    ),
    pytest.param(CONTROL, parsed(finding("unrelated text")), False, id="needs-work-on-control"),
]

LOCATED_CATCH_CASES = [
    pytest.param(
        DEFECT, parsed(finding("tests removed from orchestra/store/db.py")), True, id="full-path"
    ),
    pytest.param(DEFECT, parsed(finding("tests removed from db.py")), True, id="basename"),
    pytest.param(DEFECT, parsed(finding("R7 is no longer covered")), True, id="requirement-id"),
    pytest.param(DEFECT, parsed(finding("see (R7)")), True, id="requirement-id-in-parens"),
    pytest.param(
        DEFECT,
        parsed(finding("unrelated", requirement="R7 is violated")),
        True,
        id="requirement-field",
    ),
    pytest.param(
        DEFECT, parsed(finding("R70 is not covered")), False, id="id-prefix-no-word-boundary"
    ),
    pytest.param(DEFECT, parsed(finding("see db.pyc")), False, id="basename-prefix-no-match"),
    pytest.param(
        DEFECT,
        parsed(finding("db.py is missing tests", blocking=False)),
        False,
        id="advisory-finding-ignored",
    ),
    pytest.param(DEFECT, parsed(finding("nothing relevant")), False, id="no-expected-name"),
    pytest.param(CONTROL, parsed(finding("db.py changed")), False, id="control-never-located"),
]

FALSE_ALARM_CASES = [
    pytest.param(CONTROL, parsed(finding("anything")), True, id="needs-work-on-control"),
    pytest.param(CONTROL, parsed(), False, id="pass-on-control"),
    pytest.param(CONTROL, parsed(finding("x", blocking=False)), False, id="advisory-on-control"),
    pytest.param(DEFECT, parsed(finding("anything")), False, id="needs-work-on-defect"),
]

INCOMPLETE_CASES = [
    pytest.param(c, Incomplete(reason), id=f"{c.kind}-{reason}")
    for c in (DEFECT, ESCAPE, CONTROL)
    for reason in ("failed", "usage_limit", "unparsable")
]


@pytest.mark.parametrize(("case_", "outcome", "expected"), VERDICT_CATCH_CASES)
def test_verdict_catch(case_: Case, outcome: Complete, expected: bool) -> None:
    assert score_call(case_, outcome).verdict_catch is expected


@pytest.mark.parametrize(("case_", "outcome", "expected"), LOCATED_CATCH_CASES)
def test_located_catch(case_: Case, outcome: Complete, expected: bool) -> None:
    assert score_call(case_, outcome).located_catch is expected


@pytest.mark.parametrize(("case_", "outcome", "expected"), FALSE_ALARM_CASES)
def test_false_alarm(case_: Case, outcome: Complete, expected: bool) -> None:
    assert score_call(case_, outcome).false_alarm is expected


@pytest.mark.parametrize(("case_", "outcome"), INCOMPLETE_CASES)
def test_incomplete_calls_are_only_incomplete(case_: Case, outcome: Incomplete) -> None:
    assert score_call(case_, outcome) == Score(incomplete=True)


@pytest.mark.parametrize("reason", ["failed", "usage_limit", "unparsable"])
def test_incomplete_calls_keep_no_catch_on_defect(reason: IncompleteReason) -> None:
    score = score_call(DEFECT, Incomplete(reason))
    assert not (score.verdict_catch or score.located_catch or score.false_alarm)
    assert score.incomplete


def test_incomplete_calls_complete_output_is_not_incomplete() -> None:
    assert score_call(DEFECT, parsed(finding("x"))).incomplete is False


def test_score_is_frozen() -> None:
    with pytest.raises(FrozenInstanceError):
        Score().verdict_catch = True  # pyright: ignore[reportAttributeAccessIssue]
