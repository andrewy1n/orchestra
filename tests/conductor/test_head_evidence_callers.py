from __future__ import annotations

import itertools
from collections.abc import Sequence
from pathlib import Path

import test_wave_end as wave_world

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor import wave, workflow
from orchestra.conductor.suite import SuitePolicy, suite_ready_for_review
from orchestra.derive import release_ready, requirement_status

_CLOCK = itertools.count()
HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
PHASE = "p"


def _record(
    record_type: str,
    subject: str,
    payload: JsonObject,
    state: str = "recorded",
    *,
    record_id: str | None = None,
    recorded_at: str | None = None,
    corrects: str | None = None,
) -> Record:
    n = next(_CLOCK)
    return {
        "id": record_id or f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {"corrects": [corrects]} if corrects else {},
        "revision": f"r{n}",
        "recorded_at": recorded_at or f"2026-11-01T00:00:{n:02d}Z",
    }


def _spec(*requirements: str) -> Record:
    return _record(
        "score:specification",
        f"{PHASE}-spec",
        {"phase": PHASE, "requirements": list(requirements)},
        "active",
    )


def _acceptance(subject: str, requirement: str = "R1") -> Record:
    return _record(
        "score:acceptance", subject, {"phase": PHASE, "requirement": requirement}, "active"
    )


def _run(
    acceptance: Record,
    result: str,
    revision: str = HEAD,
    *,
    criterion: str | None = None,
    **extra: str,
) -> Record:
    return _record(
        "tuner:check-run",
        acceptance["subject"],
        {
            "criterion_id": acceptance["id"] if criterion is None else criterion,
            "result": result,
            "revision": revision,
            **extra,
        },
        **{k: v for k, v in extra.items() if k in ("record_id", "recorded_at")},
    )


def _status(records: Sequence[Record], head: str | None = HEAD) -> str:
    return requirement_status(list(records), PHASE, head)["R1"].status


def test_requirement_status_verified_by_passing_run_at_head() -> None:
    acceptance = _acceptance("a1")
    assert _status([_spec("R1"), acceptance, _run(acceptance, "pass")]) == "verified"


def test_requirement_status_ignores_runs_at_other_revisions() -> None:
    acceptance = _acceptance("a1")
    records = [_spec("R1"), acceptance, _run(acceptance, "pass", "f" * 40)]
    assert _status(records) == "unverified"


def test_requirement_status_without_head_uses_runs_at_any_revision() -> None:
    acceptance = _acceptance("a1")
    records = [_spec("R1"), acceptance, _run(acceptance, "pass", "f" * 40)]
    assert _status(records, None) == "verified"


def test_requirement_status_failed_when_latest_run_fails() -> None:
    acceptance = _acceptance("a1")
    records = [_spec("R1"), acceptance, _run(acceptance, "pass"), _run(acceptance, "fail")]
    assert _status(records) == "failed"


def test_requirement_status_needs_every_acceptance_of_the_requirement() -> None:
    first, second = _acceptance("a1"), _acceptance("a2")
    records = [_spec("R1"), first, second, _run(first, "pass")]
    assert _status(records) == "unverified"


def test_requirement_status_keeps_written_assessment_override() -> None:
    acceptance = _acceptance("a1")
    passing = _run(acceptance, "pass")
    assessment = _record(
        "conductor:assessment",
        PHASE,
        {"phase": PHASE, "requirement": "R1", "status": "failed"},
        "active",
    )
    records = [_spec("R1"), acceptance, passing, assessment]
    status = requirement_status(records, PHASE, HEAD)["R1"]
    assert status.status == "failed"
    assert status.assessed == "failed"


def test_requirement_status_release_ready_follows_the_same_rules() -> None:
    acceptance = _acceptance("a1")
    prefix = _run(acceptance, "pass", HEAD[:7])
    assert release_ready([_spec("R1"), acceptance, prefix], PHASE, HEAD)
    assert not release_ready([_spec("R1"), acceptance, prefix], PHASE, "0" * 40)


def test_short_prefix_verifies_requirement_and_wave(tmp_path: Path) -> None:
    acceptance = _acceptance("a1")
    assert _status([_spec("R1"), acceptance, _run(acceptance, "pass", HEAD[:7])]) == "verified"

    project, repo = _landed_task(tmp_path)
    tip = wave_world._git(repo, "rev-parse", "task/ph/a")
    _correct_run(project, "a", {"revision": tip[:7]})
    assert wave.end(project, repo, wave_world.PHASE).merged == ("a",)


def test_corrected_check_run_ignored_by_status_and_wave(tmp_path: Path) -> None:
    acceptance = _acceptance("a1")
    passing = _run(acceptance, "pass")
    correction = _record(
        "tuner:check-run",
        "a1",
        {"criterion_id": acceptance["id"], "result": "pass", "revision": "f" * 40},
        corrects=passing["id"],
    )
    assert _status([_spec("R1"), acceptance, passing, correction]) == "unverified"

    project, repo = _landed_task(tmp_path)
    _correct_run(project, "a", {"revision": "0" * 40})
    result = wave.end(project, repo, wave_world.PHASE)
    assert result.skipped == (("a", "checks did not pass"),)


def test_acceptance_subject_check_run_counts_in_status_and_wave(tmp_path: Path) -> None:
    acceptance = _acceptance("a1")
    by_subject = _run(acceptance, "pass", criterion="a1")
    assert _status([_spec("R1"), acceptance, by_subject]) == "verified"

    project, repo = _landed_task(tmp_path)
    _correct_run(project, "a", {"criterion_id": "a"})
    assert wave.end(project, repo, wave_world.PHASE).merged == ("a",)


def test_timestamp_tie_resolves_by_record_id_in_status() -> None:
    acceptance = _acceptance("a1")
    stamp = "2026-11-01T00:00:00Z"
    passing = _record(
        "tuner:check-run",
        "a1",
        {"criterion_id": acceptance["id"], "result": "pass", "revision": HEAD},
        record_id="<run-b>",
        recorded_at=stamp,
    )
    failing = _record(
        "tuner:check-run",
        "a1",
        {"criterion_id": acceptance["id"], "result": "fail", "revision": HEAD},
        record_id="<run-a>",
        recorded_at=stamp,
    )
    assert _status([_spec("R1"), acceptance, passing, failing]) == "verified"
    assert _status([_spec("R1"), acceptance, failing, passing]) == "verified"


def _landed_task(tmp_path: Path) -> tuple[Project, Path]:
    project, repo = wave_world._world(tmp_path, {"a": "true"})
    wave_world._land(project, repo, "a", "a.txt", "a\n")
    return project, repo


def _correct_run(project: Project, task: str, payload: JsonObject) -> None:
    acceptance = project.resolve("score:acceptance", task)
    runs = [
        run
        for run in project.list("tuner:check-run")
        if run["payload"].get("criterion_id") == acceptance["id"]
    ]
    assert len(runs) == 1
    project.correct(runs[0]["id"], payload=payload)


def test_wave_end_merges_task_with_passing_run_at_tip(tmp_path: Path) -> None:
    project, repo = _landed_task(tmp_path)
    assert wave.end(project, repo, wave_world.PHASE).merged == ("a",)


def test_wave_end_skips_task_whose_latest_run_at_tip_fails(tmp_path: Path) -> None:
    project, repo = wave_world._world(tmp_path, {"a": "false"})
    wave_world._land(project, repo, "a", "a.txt", "a\n")
    result = wave.end(project, repo, wave_world.PHASE)
    assert result.skipped == (("a", "checks did not pass"),)


def test_wave_end_skips_task_without_run_at_tip(tmp_path: Path) -> None:
    project, repo = _landed_task(tmp_path)
    _correct_run(project, "a", {"revision": "0" * 40})
    assert wave.end(project, repo, wave_world.PHASE).merged == ()


def _phase(state: str = "done") -> Record:
    return _record("score:phase", PHASE, {"effort": "e"}, state)


def _ready(records: Sequence[Record]) -> tuple[bool, str]:
    return workflow._verification_ready(list(records), PHASE)


def test_workflow_readiness_holds_with_a_passing_run_at_any_revision() -> None:
    acceptance = _acceptance("a1")
    assert _ready([_phase(), acceptance, _run(acceptance, "pass", "f" * 40)]) == (True, "")


def test_workflow_readiness_requires_a_run_for_each_acceptance() -> None:
    first, second = _acceptance("a1"), _acceptance("a2")
    ready, reason = _ready([_phase(), first, second, _run(first, "pass")])
    assert not ready
    assert "a2" in reason


def test_workflow_readiness_fails_when_latest_run_is_not_pass() -> None:
    acceptance = _acceptance("a1")
    ready, reason = _ready(
        [_phase(), acceptance, _run(acceptance, "pass"), _run(acceptance, "fail")]
    )
    assert not ready
    assert "a1" in reason


def test_workflow_readiness_ignores_corrected_runs() -> None:
    acceptance = _acceptance("a1")
    failing = _run(acceptance, "fail")
    correction = _record(
        "tuner:check-run",
        "a1",
        {"criterion_id": acceptance["id"], "result": "pass", "revision": HEAD},
        corrects=failing["id"],
    )
    assert _ready([_phase(), acceptance, failing, correction]) == (True, "")


def _suite_run(revision: str, result: str, **payload: str) -> Record:
    return _record(
        "tuner:check-run",
        f"{PHASE}-suite",
        {
            "criterion_id": f"{PHASE}-suite",
            "evidence_kind": "integration",
            "revision": revision,
            "result": result,
            **payload,
        },
    )


def _refusal(policy: SuitePolicy, runs: Sequence[Record]) -> str:
    return suite_ready_for_review(policy, runs, phase_slug=PHASE, phase_head=HEAD)


BLOCKING = SuitePolicy(mode="full", command="true", gate="required")
ADVISORY = SuitePolicy(mode="full", command="true", gate="advisory")


def test_suite_readiness_accepts_short_revision_prefix() -> None:
    assert _refusal(BLOCKING, [_suite_run(HEAD[:7], "pass")]) == ""


def test_suite_readiness_reports_missing_run_at_head() -> None:
    assert (
        _refusal(BLOCKING, [_suite_run("f" * 40, "pass")])
        == f"no {PHASE}-suite check-run at {HEAD}"
    )


def test_suite_readiness_ignores_corrected_runs() -> None:
    passing = _suite_run(HEAD, "pass")
    correction = _record(
        "tuner:check-run",
        f"{PHASE}-suite",
        {
            "criterion_id": f"{PHASE}-suite",
            "evidence_kind": "integration",
            "revision": "f" * 40,
            "result": "pass",
        },
        corrects=passing["id"],
    )
    assert _refusal(BLOCKING, [passing, correction]) == f"no {PHASE}-suite check-run at {HEAD}"


def test_suite_readiness_blocking_policy_requires_a_pass() -> None:
    assert (
        _refusal(BLOCKING, [_suite_run(HEAD, "fail")])
        == f"{PHASE}-suite check-run at {HEAD} did not pass"
    )


def test_suite_readiness_advisory_policy_accepts_a_failing_run() -> None:
    assert _refusal(ADVISORY, [_suite_run(HEAD, "fail")]) == ""
