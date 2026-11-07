from __future__ import annotations

import pytest

from orchestra.conductor import reviewer

INTEGRATION = """integration:
  interfaces: parser feeds routing
  assumptions: none
  invariants: parent is the single writer
  conflicts:
"""


def finding_block(
    *,
    task: str = "task-a",
    kind: str = "behavior-bug",
    severity: str = "major",
    blocking: str | None = "true",
    requirement: str | None = "R2: findings carry a basis",
    trigger: str | None = "a blocking finding omits its trigger",
    consequence: str | None = "the phase blocks without a stated cause",
    escape: str | None = None,
) -> str:
    lines = [
        f"  - task: {task}",
        f"    kind: {kind}",
        "    expected: the spec holds",
        "    observed: the diff differs",
        f"    severity: {severity}",
    ]
    for key, value in (
        ("blocking", blocking),
        ("requirement", requirement),
        ("trigger", trigger),
        ("consequence", consequence),
        ("escape", escape),
    ):
        if value is not None:
            lines.append(f"    {key}: {value}")
    return "\n".join(lines) + "\n"


def review(verdict: str, *blocks: str) -> str:
    body = "".join(blocks) if blocks else " []\n"
    return f"verdict: {verdict}\nfindings:\n{body}{INTEGRATION}"


def test_pass_with_only_advisory_findings_returns_pass() -> None:
    text = review("NEEDS_WORK", finding_block(blocking="false", severity="minor"))
    parsed = reviewer.validate_reviewer_output(text)
    assert parsed["verdict"] == "PASS"
    assert len(parsed["findings"]) == 1
    assert parsed["findings"][0].get("blocking") is False


def test_pass_with_only_advisory_findings_accepts_a_pass_verdict_line() -> None:
    text = review("PASS", finding_block(blocking="false", severity="minor"))
    assert reviewer.validate_reviewer_output(text)["verdict"] == "PASS"


def test_blocking_finding_names_requirement() -> None:
    text = review("NEEDS_WORK", finding_block(requirement=None))
    parsed = reviewer.validate_reviewer_output(text)
    assert parsed["findings"][0].get("blocking") is False
    assert parsed["verdict"] == "PASS"


def test_blocking_finding_with_requirement_stays_blocking() -> None:
    parsed = reviewer.validate_reviewer_output(review("NEEDS_WORK", finding_block()))
    assert parsed["findings"][0].get("requirement") == "R2: findings carry a basis"
    assert parsed["findings"][0].get("blocking") is True
    assert parsed["verdict"] == "NEEDS_WORK"


def test_blocking_finding_names_trigger() -> None:
    parsed = reviewer.validate_reviewer_output(review("NEEDS_WORK", finding_block(trigger=None)))
    assert parsed["findings"][0].get("blocking") is False


def test_blocking_finding_names_consequence() -> None:
    parsed = reviewer.validate_reviewer_output(
        review("NEEDS_WORK", finding_block(consequence=None))
    )
    assert parsed["findings"][0].get("blocking") is False


def test_blocking_missing_test_finding_names_escape() -> None:
    bare = finding_block(kind="missing-test", escape=None)
    assert (
        reviewer.validate_reviewer_output(review("NEEDS_WORK", bare))["findings"][0].get("blocking")
        is False
    )
    full = finding_block(kind="missing-test", escape="a regression in routing passes every test")
    parsed = reviewer.validate_reviewer_output(review("NEEDS_WORK", full))
    assert parsed["findings"][0].get("blocking") is True
    assert parsed["verdict"] == "NEEDS_WORK"


def test_non_test_finding_needs_no_escape() -> None:
    parsed = reviewer.validate_reviewer_output(review("NEEDS_WORK", finding_block(escape=None)))
    assert parsed["findings"][0].get("blocking") is True


def test_incomplete_blocking_finding_demotes_to_advisory_and_is_listed() -> None:
    parsed = reviewer.validate_reviewer_output(
        review("NEEDS_WORK", finding_block(task="task-b", trigger=None))
    )
    assert parsed["findings"][0].get("blocking") is False
    assert parsed["demoted"] == ["task-b:behavior-bug"]


def test_complete_blocking_finding_is_not_listed_as_demoted() -> None:
    parsed = reviewer.validate_reviewer_output(review("NEEDS_WORK", finding_block()))
    assert parsed["demoted"] == []


def test_derives_verdict_from_findings_not_the_verdict_line() -> None:
    blocking = review("PASS", finding_block())
    assert reviewer.validate_reviewer_output(blocking)["verdict"] == "NEEDS_WORK"
    advisory = review("NEEDS_WORK", finding_block(blocking="false", severity="minor"))
    assert reviewer.validate_reviewer_output(advisory)["verdict"] == "PASS"
    assert reviewer.validate_reviewer_output(review("NEEDS_WORK"))["verdict"] == "PASS"


def test_derives_verdict_needs_work_for_a_judgment_finding() -> None:
    text = review(
        "PASS",
        finding_block(
            severity="judgment",
            blocking="false",
            requirement=None,
            trigger=None,
            consequence=None,
        ),
    )
    parsed = reviewer.validate_reviewer_output(text)
    assert parsed["verdict"] == "NEEDS_WORK"
    assert parsed["findings"][0].get("blocking") is True


def test_finding_without_a_blocking_line_is_rejected() -> None:
    with pytest.raises(ValueError, match="blocking"):
        reviewer.validate_reviewer_output(review("NEEDS_WORK", finding_block(blocking=None)))


def test_finding_with_a_malformed_blocking_value_is_rejected() -> None:
    with pytest.raises(ValueError, match="blocking"):
        reviewer.validate_reviewer_output(review("NEEDS_WORK", finding_block(blocking="maybe")))


def test_verdict_line_must_still_be_pass_or_needs_work() -> None:
    with pytest.raises(ValueError, match="verdict"):
        reviewer.validate_reviewer_output(review("MAYBE"))
