from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record, get_object
from orchestra.conductor.tasks.redispatch import task_redispatch
from orchestra.conductor.tasks.redispatch.failure_key import failure_key
from orchestra.conductor.tasks.redispatch.task_redispatch import RedispatchError

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


def _fail(project: Project, criterion: str, nodes: list[str]) -> None:
    create(
        project,
        "tuner:check-run",
        TASK,
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


def _counts_of(record: Record) -> JsonObject:
    return get_object(record_payload(record), "failure_attempts") or {}


def _counts(project: Project) -> JsonObject:
    return _counts_of(project.resolve("score:work-item", TASK))


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
    assert retried["payload"]["failure_attempts"] == {key: 1}


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

    retried = _retry(project)

    assert _counts_of(retried)[failure_key("crit", NODES_B)] == 1


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

    retried = _retry(project)

    assert retried["payload"]["failure_attempts"] == {failure_key("crit", NODES_A): 3}
