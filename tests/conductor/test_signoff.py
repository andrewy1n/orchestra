from __future__ import annotations

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.phases.workflow.signoff import awaiting_signoff

_N = [0]


def _record(record_type: str, subject: str, payload: JsonObject, state: str) -> Record:
    _N[0] += 1
    return {
        "id": f"<{record_type}:{subject}-{_N[0]}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{_N[0]}",
        "recorded_at": f"2026-11-01T00:00:{_N[0]:02d}Z",
    }


def _task(subject: str, state: str = "planned", phase: str = "p") -> Record:
    return _record("score:work-item", subject, {"phase": phase, "effort": "e"}, state)


def _acceptance(subject: str, state: str = "active") -> Record:
    return _record(
        "score:acceptance",
        subject,
        {"phase": "p", "effort": "e", "method": "manual", "criterion": "c"},
        state,
    )


def _run(
    acceptance: Record,
    result: str = "pass",
    method: str = "manual",
    signed_by: str = "",
    state: str = "recorded",
) -> Record:
    return _record(
        "tuner:check-run",
        acceptance["subject"],
        {
            "criterion_id": acceptance["id"],
            "result": result,
            "method": method,
            "signed_by": signed_by,
            "effort": "e",
            "revision": "abc",
        },
        state,
    )


def test_phase_awaits_signoff_when_every_open_task_has_an_unsigned_manual_pass() -> None:
    tasks = [_task("a"), _task("b")]
    acceptances = [_acceptance("a-acc"), _acceptance("b-acc")]
    checks = [_run(acceptances[0]), _run(acceptances[1])]
    assert awaiting_signoff("in_progress", tasks, tasks, acceptances, checks)


def test_phase_does_not_await_signoff_when_one_open_task_lacks_a_passing_run() -> None:
    tasks = [_task("a"), _task("b")]
    acceptances = [_acceptance("a-acc"), _acceptance("b-acc")]
    checks = [_run(acceptances[0]), _run(acceptances[1], result="fail")]
    assert not awaiting_signoff("in_progress", tasks, tasks, acceptances, checks)


def test_phase_does_not_await_signoff_when_the_manual_run_is_signed() -> None:
    tasks = [_task("a")]
    acceptances = [_acceptance("a-acc")]
    checks = [_run(acceptances[0], signed_by="andrew")]
    assert not awaiting_signoff("in_progress", tasks, tasks, acceptances, checks)


def test_phase_does_not_await_signoff_when_the_passing_run_is_not_manual() -> None:
    tasks = [_task("a")]
    acceptances = [_acceptance("a-acc")]
    checks = [_run(acceptances[0], method="check")]
    assert not awaiting_signoff("in_progress", tasks, tasks, acceptances, checks)


def test_phase_does_not_await_signoff_when_a_task_has_no_acceptance() -> None:
    tasks = [_task("a")]
    assert not awaiting_signoff("in_progress", tasks, tasks, [], [])


def test_phase_does_not_await_signoff_when_an_acceptance_has_no_run() -> None:
    tasks = [_task("a")]
    acceptances = [_acceptance("a-acc")]
    assert not awaiting_signoff("in_progress", tasks, tasks, acceptances, [])


def test_phase_does_not_await_signoff_when_it_is_done() -> None:
    tasks = [_task("a")]
    acceptances = [_acceptance("a-acc")]
    assert not awaiting_signoff("done", tasks, tasks, acceptances, [_run(acceptances[0])])


def test_phase_does_not_await_signoff_without_open_tasks() -> None:
    tasks = [_task("a", state="done")]
    acceptances = [_acceptance("a-acc")]
    assert not awaiting_signoff("in_progress", tasks, tasks, acceptances, [_run(acceptances[0])])


def test_signoff_ignores_done_tasks_and_inactive_acceptances() -> None:
    open_task = _task("a")
    done_task = _task("b", state="done")
    tasks = [open_task, done_task]
    live = _acceptance("a-acc")
    retired = _acceptance("a-old", state="superseded")
    checks = [_run(live)]
    assert awaiting_signoff("in_progress", tasks, tasks, [live, retired], checks)


def test_signoff_uses_the_latest_active_run_per_acceptance() -> None:
    tasks = [_task("a")]
    acceptance = _acceptance("a-acc")
    failed = _run(acceptance, result="fail")
    passed = _run(acceptance)
    retracted = _run(acceptance, result="fail", state="retracted")
    assert awaiting_signoff("in_progress", tasks, tasks, [acceptance], [failed, passed, retracted])
    failed_later = _run(acceptance, result="fail")
    assert not awaiting_signoff(
        "in_progress", tasks, tasks, [acceptance], [passed, failed_later, retracted]
    )
