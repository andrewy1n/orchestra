"""Head evidence answers over records read from a temporary store."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conductor_support import EFFORT, HEAD, PHASE, Cli, Phase, seed

from orchestra.canon.project import open_store
from orchestra.canon.types import Record
from orchestra.conductor import head_evidence
from orchestra.conductor.head_evidence import EvidenceIndex

OTHER_HEAD = "b" * 40


@pytest.fixture
def phase(store: Path, cli: Cli) -> Phase:
    return seed(store, cli, review=False, runner_check=False)


def _records(phase: Phase) -> list[Record]:
    return open_store(phase.store).records()


def _index(phase: Phase) -> EvidenceIndex:
    return EvidenceIndex(_records(phase))


def _by_id(phase: Phase, record_id: str) -> Record:
    return next(r for r in _records(phase) if r["id"] == record_id)


def _acceptance(phase: Phase) -> Record:
    return _by_id(phase, phase.acceptance["id"])


def _at(record: Record, recorded_at: str, record_id: str | None = None) -> Record:
    return {**record, "recorded_at": recorded_at, "id": record_id or record["id"]}


def _correct(phase: Phase, record: dict) -> None:
    result = phase.cli(
        "correct",
        "--type",
        "tuner:check-run",
        "--id",
        record["id"],
        "--payload",
        json.dumps({"result": "pass"}),
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_ownership_matches_acceptance_id(phase: Phase) -> None:
    run = phase.check_run(criterion=phase.acceptance["id"])
    answer = head_evidence.acceptance_latest(_index(phase), _acceptance(phase), None)
    assert answer.holds
    assert answer.run is not None
    assert answer.run["id"] == run["id"]


def test_ownership_matches_acceptance_subject(phase: Phase) -> None:
    run = phase.check_run(criterion=phase.acceptance["subject"])
    answer = head_evidence.acceptance_latest(_index(phase), _acceptance(phase), None)
    assert answer.run is not None
    assert answer.run["id"] == run["id"]


def test_ownership_ignores_other_acceptance(phase: Phase) -> None:
    phase.check_run(criterion="someone-else")
    answer = head_evidence.acceptance_latest(_index(phase), _acceptance(phase), None)
    assert not answer.holds
    assert answer.run is None


def test_corrected_check_run_is_never_evidence(phase: Phase) -> None:
    run = phase.check_run("pass")
    _correct(phase, run)
    index = _index(phase)
    answer = head_evidence.acceptance_latest(index, _acceptance(phase), None)
    assert answer.run is not None
    assert answer.run["id"] != run["id"]
    assert all(r["id"] != run["id"] for r in index.check_runs)


def test_corrected_review_check_run_is_never_evidence(phase: Phase) -> None:
    run = phase.review("pass")
    _correct(phase, run)
    answer = head_evidence.review_at_head(_index(phase), PHASE, EFFORT, HEAD)
    assert answer.run is None or answer.run["id"] != run["id"]


def test_latest_order_takes_greatest_recorded_at(phase: Phase) -> None:
    first = phase.check_run("pass", earlier=True)
    second = phase.check_run("fail")
    index = _index(phase)
    latest = head_evidence.latest(index.check_runs)
    assert latest is not None
    assert latest["id"] == second["id"]
    assert first["id"] != second["id"]


def test_latest_order_breaks_timestamp_tie_by_record_id(phase: Phase) -> None:
    one = phase.check_run("pass")
    two = phase.check_run("fail")
    low, high = sorted([one["id"], two["id"]])
    stamp = "2026-11-01T00:00:00Z"
    runs = [_at(_by_id(phase, high), stamp), _at(_by_id(phase, low), stamp)]
    latest = head_evidence.latest(runs)
    assert latest is not None
    assert latest["id"] == high
    reversed_latest = head_evidence.latest(list(reversed(runs)))
    assert reversed_latest is not None
    assert reversed_latest["id"] == high


def test_at_head_accepts_seven_character_prefix(phase: Phase) -> None:
    phase.check_run("pass", revision=HEAD[:7])
    answer = head_evidence.acceptance_latest(_index(phase), _acceptance(phase), HEAD)
    assert answer.holds


def test_at_head_rejects_six_character_prefix(phase: Phase) -> None:
    phase.check_run("pass", revision=HEAD[:6])
    answer = head_evidence.acceptance_latest(_index(phase), _acceptance(phase), HEAD)
    assert not answer.holds


def test_at_head_ignores_other_revision(phase: Phase) -> None:
    phase.check_run("pass", revision=OTHER_HEAD)
    answer = head_evidence.acceptance_latest(_index(phase), _acceptance(phase), HEAD)
    assert not answer.holds
    assert answer.run is None


def test_no_head_makes_every_revision_a_candidate(phase: Phase) -> None:
    phase.check_run("pass", revision=OTHER_HEAD)
    answer = head_evidence.acceptance_latest(_index(phase), _acceptance(phase), None)
    assert answer.holds


def test_no_head_uses_latest_across_revisions(phase: Phase) -> None:
    phase.check_run("pass", revision=HEAD, earlier=True)
    phase.check_run("fail", revision=OTHER_HEAD)
    answer = head_evidence.acceptance_latest(_index(phase), _acceptance(phase), None)
    assert not answer.holds


def test_latest_pass_fails_on_later_fail_at_same_head(phase: Phase) -> None:
    phase.check_run("pass", earlier=True)
    later = phase.check_run("fail")
    answer = head_evidence.acceptance_latest(_index(phase), _acceptance(phase), HEAD)
    assert not answer.holds
    assert answer.run is not None
    assert answer.run["id"] == later["id"]
    assert "fail" in answer.reason


def test_latest_pass_holds_on_latest_pass(phase: Phase) -> None:
    phase.check_run("fail", earlier=True)
    latest = phase.check_run("pass")
    answer = head_evidence.acceptance_latest(_index(phase), _acceptance(phase), HEAD)
    assert answer.holds
    assert answer.run is not None
    assert answer.run["id"] == latest["id"]
    assert answer.reason == ""


def test_runner_holds_for_passing_orchestra_run_at_head(phase: Phase) -> None:
    run = phase.check_run("pass", runner=True)
    answer = head_evidence.acceptance_runner_at_head(_index(phase), _acceptance(phase), HEAD)
    assert answer.holds
    assert answer.run is not None
    assert answer.run["id"] == run["id"]


def test_runner_fails_for_another_runner(phase: Phase) -> None:
    phase.check_run("pass", runner=False)
    answer = head_evidence.acceptance_runner_at_head(_index(phase), _acceptance(phase), HEAD)
    assert not answer.holds
    assert answer.reason


def test_runner_holds_despite_later_fail_at_head(phase: Phase) -> None:
    phase.check_run("pass", runner=True, earlier=True)
    phase.check_run("fail", runner=True)
    answer = head_evidence.acceptance_runner_at_head(_index(phase), _acceptance(phase), HEAD)
    assert answer.holds


def test_runner_fails_at_other_revision(phase: Phase) -> None:
    phase.check_run("pass", runner=True, revision=OTHER_HEAD)
    answer = head_evidence.acceptance_runner_at_head(_index(phase), _acceptance(phase), HEAD)
    assert not answer.holds


def test_runner_no_head_accepts_any_revision(phase: Phase) -> None:
    phase.check_run("pass", runner=True, revision=OTHER_HEAD)
    answer = head_evidence.acceptance_runner_at_head(_index(phase), _acceptance(phase), None)
    assert answer.holds


def test_review_check_run_selects_method_effort_and_subject(phase: Phase) -> None:
    run = phase.review("pass")
    runs = head_evidence.review_check_runs(_index(phase), PHASE, EFFORT)
    assert [r["id"] for r in runs] == [run["id"]]


def test_review_check_run_matches_criterion_id_alone(phase: Phase) -> None:
    run = phase.check_run(
        "pass", criterion=f"{PHASE}-review", method="review", runner=False, subject="other"
    )
    runs = head_evidence.review_check_runs(_index(phase), PHASE, EFFORT)
    assert [r["id"] for r in runs] == [run["id"]]


def test_review_check_run_excludes_another_phase(phase: Phase) -> None:
    phase.check_run(
        "pass",
        criterion="other-review",
        method="review",
        runner=False,
        subject="other-review",
    )
    assert head_evidence.review_check_runs(_index(phase), PHASE, EFFORT) == []


def test_review_check_run_excludes_another_effort(phase: Phase) -> None:
    phase.review("pass")
    assert head_evidence.review_check_runs(_index(phase), PHASE, "other-effort") == []


def test_review_check_run_excludes_another_method(phase: Phase) -> None:
    phase.check_run("pass", criterion=f"{PHASE}-review", method="check", runner=False)
    assert head_evidence.review_check_runs(_index(phase), PHASE, EFFORT) == []


def test_review_answer_holds_on_latest_pass_at_head(phase: Phase) -> None:
    phase.review("fail", earlier=True)
    run = phase.review("pass")
    answer = head_evidence.review_at_head(_index(phase), PHASE, EFFORT, HEAD)
    assert answer.holds
    assert answer.run is not None
    assert answer.run["id"] == run["id"]


def test_review_answer_fails_on_later_fail_at_head(phase: Phase) -> None:
    phase.review("pass", earlier=True)
    phase.review("fail")
    answer = head_evidence.review_at_head(_index(phase), PHASE, EFFORT, HEAD)
    assert not answer.holds
    assert answer.reason


def test_review_answer_fails_at_other_head(phase: Phase) -> None:
    phase.review("pass", revision=OTHER_HEAD)
    answer = head_evidence.review_at_head(_index(phase), PHASE, EFFORT, HEAD)
    assert not answer.holds


def test_review_answer_latest_review_ignores_head(phase: Phase) -> None:
    phase.review("pass", revision=HEAD, earlier=True)
    run = phase.review("fail", revision=OTHER_HEAD)
    latest = head_evidence.latest_review(_index(phase), PHASE, EFFORT)
    assert latest is not None
    assert latest["id"] == run["id"]


def test_review_answer_latest_review_is_none_without_review(phase: Phase) -> None:
    assert head_evidence.latest_review(_index(phase), PHASE, EFFORT) is None


def test_suite_check_run_requires_integration_kind(phase: Phase) -> None:
    run = phase.suite_run("pass")
    phase.check_run(
        "pass", criterion=f"{PHASE}-suite", subject=f"{PHASE}-suite", evidence_kind="review"
    )
    runs = head_evidence.suite_check_runs(_index(phase), PHASE)
    assert [r["id"] for r in runs] == [run["id"]]


def test_suite_check_run_excludes_another_phase(phase: Phase) -> None:
    phase.check_run(
        "pass", criterion="other-suite", subject="other-suite", evidence_kind="integration"
    )
    assert head_evidence.suite_check_runs(_index(phase), PHASE) == []


def test_suite_answer_holds_when_a_suite_run_passes_at_head(phase: Phase) -> None:
    run = phase.suite_run("pass")
    answer = head_evidence.suite_at_head(_index(phase), PHASE, HEAD)
    assert answer.holds
    assert answer.run is not None
    assert answer.run["id"] == run["id"]


def test_suite_answer_fails_at_other_head(phase: Phase) -> None:
    phase.suite_run("pass", revision=OTHER_HEAD)
    answer = head_evidence.suite_at_head(_index(phase), PHASE, HEAD)
    assert not answer.holds


def test_suite_answer_fails_when_suite_run_fails(phase: Phase) -> None:
    phase.suite_run("fail")
    answer = head_evidence.suite_at_head(_index(phase), PHASE, HEAD)
    assert not answer.holds
    assert answer.run is not None


def test_answer_shape_without_evidence_has_reason_and_no_run(phase: Phase) -> None:
    index = _index(phase)
    answers = [
        head_evidence.acceptance_latest(index, _acceptance(phase), HEAD),
        head_evidence.acceptance_runner_at_head(index, _acceptance(phase), HEAD),
        head_evidence.review_at_head(index, PHASE, EFFORT, HEAD),
        head_evidence.suite_at_head(index, PHASE, HEAD),
    ]
    for answer in answers:
        assert not answer.holds
        assert answer.run is None
        assert answer.reason


def test_answer_shape_holding_answer_has_run_and_no_reason(phase: Phase) -> None:
    phase.check_run("pass")
    phase.review("pass")
    phase.suite_run("pass")
    index = _index(phase)
    answers = [
        head_evidence.acceptance_latest(index, _acceptance(phase), HEAD),
        head_evidence.acceptance_runner_at_head(index, _acceptance(phase), HEAD),
        head_evidence.review_at_head(index, PHASE, EFFORT, HEAD),
        head_evidence.suite_at_head(index, PHASE, HEAD),
    ]
    for answer in answers:
        assert answer.holds
        assert answer.run is not None
        assert answer.reason == ""


def test_answer_shape_suite_naming_rule_lives_in_head_evidence() -> None:
    from orchestra.conductor import suite

    assert head_evidence.suite_subject("p1") == "p1-suite"
    assert head_evidence.suite_subject("p1-suite") == "p1-suite"
    assert suite.suite_subject is head_evidence.suite_subject
    assert suite.EVIDENCE_KIND == head_evidence.SUITE_EVIDENCE_KIND
