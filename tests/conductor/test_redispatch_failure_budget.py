from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import JsonValue, Record
from orchestra.conductor.tasks.redispatch import task_redispatch
from orchestra.conductor.tasks.redispatch.failure_key import failure_key
from orchestra.conductor.tasks.redispatch.task_redispatch import RedispatchError
from orchestra.tuner.evidence.record_facts import RecordShapeError, check_run_failing_nodes

PHASE = "budget-phase"
EFFORT = "budget-effort"
TASK = "task"
LANDING = "\n\n## Landing\n\nbranch: phase/budget-phase\nbase: main\n"
BODY = "## Problem\n\nProblem.\n\n## Approach\n\nApproach.\n\n## Exit criteria\n\nCriteria."
NODES_A = ["tests/test_a.py::test_one", "tests/test_a.py::test_two"]
NODES_B = ["tests/test_b.py::test_other"]


def _world(tmp_path: Path, run_facts: str = "") -> Project:
    project = make_project(tmp_path)
    create(project, "score:effort", EFFORT, {"goal": "Budget", "kind": "deliver"})
    create(
        project,
        "score:phase",
        PHASE,
        {"title": "Budget", "ordinal": 1, "effort": EFFORT},
        BODY + run_facts + LANDING,
    )
    create(
        project,
        "score:work-item",
        TASK,
        {
            "title": TASK,
            "phase": PHASE,
            "kind": "deliver",
            "assignee": "subagent",
            "effort": EFFORT,
        },
        "## Description\n\nDo it.\n\n## Approach\n\nJust do it.",
    )
    item = project.resolve("score:work-item", TASK)
    project.update(item["id"], record_type="score:work-item", transition="in_progress")
    return project


def _fail(project: Project, criterion: str, nodes: list[str], subject: str = TASK) -> None:
    create(
        project,
        "tuner:check-run",
        subject,
        {
            "criterion_id": criterion,
            "result": "fail",
            "method": "tdd",
            "effort": EFFORT,
            "failing_node_ids": nodes,
            "revision": "abc123",
            "signed_by": "",
        },
    )


def _retry(project: Project):
    item = project.resolve("score:work-item", TASK)
    return task_redispatch.redispatch(project, TASK, expected_revision=item["revision"])


def _counts(project: Project) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in project.list("conductor:redispatch-attempt"):
        payload = record_payload(event)
        if payload.get("work_item") == TASK:
            key = str(payload.get("failure_key"))
            counts[key] = counts.get(key, 0) + 1
    return counts


def test_failure_key_is_a_sha256_hex_digest() -> None:
    assert re.fullmatch(r"[0-9a-f]{64}", failure_key("crit", NODES_A))


def test_failure_key_ignores_node_id_order() -> None:
    assert failure_key("crit", NODES_A) == failure_key("crit", list(reversed(NODES_A)))


def test_failure_key_differs_when_criterion_id_differs() -> None:
    assert failure_key("crit-1", NODES_A) != failure_key("crit-2", NODES_A)


def test_failure_key_differs_when_failing_node_ids_differ() -> None:
    assert failure_key("crit", NODES_A) != failure_key("crit", NODES_B)


def test_failure_key_is_not_a_plain_hash_of_the_criterion_alone() -> None:
    assert failure_key("crit", NODES_A) != hashlib.sha256(b"crit").hexdigest()


def test_redispatch_counts_attempts_under_the_failure_key(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _fail(project, "crit", NODES_A)

    retried = _retry(project)

    key = failure_key("crit", NODES_A)
    assert retried["payload"]["attempts"] == 1
    assert _counts(project) == {key: 1}


def test_redispatch_refuses_the_same_failure_after_the_default_budget(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _fail(project, "crit", NODES_A)
    _retry(project)
    _retry(project)

    with pytest.raises(RedispatchError):
        _retry(project)

    assert _counts(project) == {failure_key("crit", NODES_A): 2}
    assert project.resolve("score:work-item", TASK)["payload"]["attempts"] == 2


def test_distinct_criterion_ids_have_separate_budgets(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _fail(project, "crit-1", NODES_A)
    _retry(project)
    _retry(project)
    _fail(project, "crit-2", NODES_A)

    _retry(project)

    assert _counts(project) == {
        failure_key("crit-1", NODES_A): 2,
        failure_key("crit-2", NODES_A): 1,
    }


def test_distinct_failing_nodes_have_separate_budgets(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _fail(project, "crit", NODES_A)
    _retry(project)
    _retry(project)
    _fail(project, "crit", NODES_B)

    _retry(project)

    assert _counts(project) == {
        failure_key("crit", NODES_A): 2,
        failure_key("crit", NODES_B): 1,
    }


def test_a_new_failure_redispatches_after_another_exhausted_its_budget(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _fail(project, "crit", NODES_A)
    _retry(project)
    _retry(project)
    with pytest.raises(RedispatchError):
        _retry(project)
    _fail(project, "crit", NODES_B)

    _retry(project)

    assert _counts(project)[failure_key("crit", NODES_B)] == 1


def test_phase_run_facts_override_the_failure_budget(tmp_path: Path) -> None:
    project = _world(tmp_path, "\n\n## Run facts\n\nretry_max_redispatches: 1\n")
    _fail(project, "crit", NODES_A)
    _retry(project)

    with pytest.raises(RedispatchError):
        _retry(project)


def test_phase_run_facts_can_raise_the_failure_budget(tmp_path: Path) -> None:
    project = _world(tmp_path, "\n\n## Run facts\n\nretry_max_redispatches: 3\n")
    _fail(project, "crit", NODES_A)
    _retry(project)
    _retry(project)

    _retry(project)

    assert _counts(project) == {failure_key("crit", NODES_A): 3}


def test_failures_of_a_suffixed_acceptance_count_against_the_failure_budget(
    tmp_path: Path,
) -> None:
    project = _world(tmp_path)
    _fail(project, "crit", NODES_A, subject=f"{TASK}-snapshots")
    _retry(project)
    _retry(project)
    with pytest.raises(RedispatchError):
        _retry(project)
    assert _counts(project)[failure_key("crit", NODES_A)] == 2


def test_a_redispatch_records_one_typed_event_with_the_new_dispatch_id(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _fail(project, "crit", NODES_A)

    retried = _retry(project)

    events = project.list("conductor:redispatch-attempt")
    assert len(events) == 1
    payload = record_payload(events[0])
    assert payload["work_item"] == TASK
    assert payload["effort"] == EFFORT
    assert payload["failure_key"] == failure_key("crit", NODES_A)
    assert payload["dispatch_id"] == record_payload(retried)["dispatch_id"]


def test_a_refused_redispatch_writes_no_event(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _fail(project, "crit", NODES_A)
    _retry(project)
    _retry(project)
    with pytest.raises(RedispatchError):
        _retry(project)

    assert len(project.list("conductor:redispatch-attempt")) == 2


def test_redispatch_without_a_failing_check_run_stops_at_the_attempt_budget(
    tmp_path: Path,
) -> None:
    project = _world(tmp_path)
    _retry(project)
    _retry(project)

    with pytest.raises(RedispatchError, match="budget"):
        _retry(project)

    assert project.resolve("score:work-item", TASK)["payload"]["attempts"] == 2


def test_a_malformed_run_fact_budget_raises(tmp_path: Path) -> None:
    project = _world(tmp_path, "\n\n## Run facts\n\nretry_max_redispatches: two\n")
    _fail(project, "crit", NODES_A)

    with pytest.raises(RedispatchError, match="retry_max_redispatches"):
        _retry(project)


def _check_run_with_nodes(value: JsonValue) -> Record:
    return {
        "id": "rec-run",
        "record_type": "tuner:check-run",
        "subject": TASK,
        "payload": {"failing_node_ids": value},
        "body": "",
        "lifecycle_state": "recorded",
        "relationships": {},
        "revision": "sha256:0",
        "recorded_at": "2026-11-27T00:00:00+00:00",
    }


def test_failing_node_ids_that_are_not_a_list_raise() -> None:
    with pytest.raises(RecordShapeError):
        check_run_failing_nodes(_check_run_with_nodes("tests/test_a.py::test_one"))


def test_failing_node_ids_with_a_non_string_item_raise() -> None:
    with pytest.raises(RecordShapeError):
        check_run_failing_nodes(_check_run_with_nodes(["tests/test_a.py::test_one", 7]))


def test_failing_node_ids_that_are_absent_give_no_nodes() -> None:
    record = _check_run_with_nodes([])
    record["payload"] = {}
    assert check_run_failing_nodes(record) == ()
