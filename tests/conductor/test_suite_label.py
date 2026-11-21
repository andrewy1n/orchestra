from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.suite_label import suite_labels, suite_status_label


def _check(
    subject: str,
    result: str,
    revision: str = "abc1234deadbeef",
    *,
    body: str = "",
    state: str = "recorded",
    kind: str = "integration",
    at: str = "2026-01-01T12:00:00+00:00",
) -> Record:
    payload: JsonObject = {
        "criterion_id": "suite",
        "revision": revision,
        "result": result,
        "effort": "alpha",
        "method": "check",
        "signed_by": "",
        "evidence_kind": kind,
    }
    return {
        "id": f"id-{subject}-{result}-{at}",
        "record_type": "tuner:check-run",
        "subject": subject,
        "lifecycle_state": state,
        "recorded_at": at,
        "payload": payload,
        "body": body,
        "relationships": {},
        "revision": "sha256:test",
    }


def test_suite_label_names_pass_with_short_revision() -> None:
    checks = [_check("p-ok-suite", "pass", "abcdef0123456789")]
    assert suite_status_label("p-ok", checks) == "suite ok@abcdef0"


def test_suite_label_names_fail_with_short_revision() -> None:
    assert suite_status_label("p-bad", [_check("p-bad-suite", "fail", "deadbeef")]) == (
        "suite fail@deadbee"
    )


def test_suite_label_reports_a_running_suite() -> None:
    checks = [_check("p-run-suite", "blocked", body="suite-running in worktree")]
    assert suite_status_label("p-run", checks) == "suite running"


def test_suite_label_reports_a_running_legacy_marker() -> None:
    checks = [_check("p-run-suite", "blocked", body="tier2-running")]
    assert suite_status_label("p-run", checks) == "suite running"


def test_suite_label_is_empty_for_blocked_without_a_running_marker() -> None:
    assert suite_status_label("p-run", [_check("p-run-suite", "blocked")]) == ""


def test_suite_label_is_empty_without_a_matching_run() -> None:
    assert suite_status_label("p-none", []) == ""
    assert suite_status_label("p-ok", [_check("other-suite", "pass")]) == ""
    assert suite_status_label("p-ok", [_check("p-ok-suite", "pass", kind="unit")]) == ""


def test_suite_label_marks_missing_revision_with_a_question_mark() -> None:
    assert suite_status_label("p-ok", [_check("p-ok-suite", "pass", "")]) == "suite ok@?"


def test_suite_label_ignores_inactive_runs() -> None:
    checks = [
        _check("p-ok-suite", "pass", "aaaaaaa", at="2026-01-01T12:00:00+00:00"),
        _check("p-ok-suite", "fail", "bbbbbbb", at="2026-01-01T12:00:05+00:00", state="superseded"),
        _check("p-ok-suite", "fail", "ccccccc", at="2026-01-01T12:00:06+00:00", state="retracted"),
    ]
    assert suite_status_label("p-ok", checks) == "suite ok@aaaaaaa"


def test_suite_label_reads_the_newest_run() -> None:
    checks = [
        _check("p-ok-suite", "fail", "aaaaaaa", at="2026-01-01T12:00:00+00:00"),
        _check("p-ok-suite", "pass", "bbbbbbb", at="2026-01-01T12:00:09+00:00"),
    ]
    assert suite_status_label("p-ok", checks) == "suite ok@bbbbbbb"


def test_suite_label_reads_a_legacy_tier2_run() -> None:
    checks = [_check("p-legacy-tier2", "pass", "feedface")]
    assert suite_status_label("p-legacy", checks) == "suite ok@feedfac"


def test_suite_label_prefers_the_suite_run_over_a_legacy_run() -> None:
    checks = [
        _check("p-pref-tier2", "fail", "deadbeef"),
        _check("p-pref-suite", "pass", "abcdef0123456789"),
    ]
    assert suite_status_label("p-pref", checks) == "suite ok@abcdef0"


def test_suite_labels_answer_each_phase_from_one_index() -> None:
    labels = suite_labels(
        [
            _check("p-one-suite", "pass", "1111111aaa"),
            _check("p-two-suite", "fail", "2222222bbb"),
        ]
    )
    assert labels.label("p-one") == "suite ok@1111111"
    assert labels.label("p-two") == "suite fail@2222222"
    assert labels.label("p-three") == ""
