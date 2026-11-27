"""Constraint outcomes carry the outcome, the constraint version, and the revision."""

from __future__ import annotations

from pathlib import Path

from canon_support import make_project

from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor.verification.standing_constraints import (
    ConstraintResult,
    constraint_outcomes,
    criterion_id,
)

EFFORT = "refunds-effort"
NAME = "stripe-sdk-isolation"
HEAD = "a" * 40
OTHER_HEAD = "b" * 40


def _project(root: Path) -> Project:
    project = make_project(root)
    project.create(
        record_type="score:effort", subject=EFFORT, payload={"goal": "Refunds", "kind": "deliver"}
    )
    return project


def _constraint(project: Project, name: str = NAME) -> Record:
    return project.create(
        record_type="score:standing-constraint",
        subject=name,
        payload={
            "area": "payments",
            "rule": "Only billing adapters import Stripe.",
            "check": "true",
        },
        body="## Basis\n\nProvider access belongs in billing adapters.\n",
    )


def _run(project: Project, constraint_id: str, result: str, revision: str = HEAD) -> Record:
    return project.create(
        record_type="tuner:check-run",
        subject=f"{NAME}-check",
        payload={
            "criterion_id": criterion_id(constraint_id),
            "revision": revision,
            "result": result,
            "effort": EFFORT,
            "method": "check",
            "runner": "orchestra",
            "signed_by": "",
        },
    )


def test_passing_check_run_at_revision_is_verified(tmp_path: Path) -> None:
    project = _project(tmp_path)
    constraint = _constraint(project)
    _run(project, constraint["id"], "pass")

    results = constraint_outcomes(project.records(), [constraint["id"]], HEAD)

    assert results == [ConstraintResult("verified", constraint["id"], HEAD)]


def test_failing_check_run_at_revision_is_violated(tmp_path: Path) -> None:
    project = _project(tmp_path)
    constraint = _constraint(project)
    _run(project, constraint["id"], "fail")

    results = constraint_outcomes(project.records(), [constraint["id"]], HEAD)

    assert results == [ConstraintResult("violated", constraint["id"], HEAD)]


def test_constraint_without_check_run_is_unverified(tmp_path: Path) -> None:
    project = _project(tmp_path)
    constraint = _constraint(project)

    results = constraint_outcomes(project.records(), [constraint["id"]], HEAD)

    assert results == [ConstraintResult("unverified", constraint["id"], HEAD)]


def test_check_run_at_another_revision_leaves_constraint_unverified(tmp_path: Path) -> None:
    project = _project(tmp_path)
    constraint = _constraint(project)
    _run(project, constraint["id"], "pass", revision=OTHER_HEAD)

    results = constraint_outcomes(project.records(), [constraint["id"]], HEAD)

    assert results == [ConstraintResult("unverified", constraint["id"], HEAD)]


def test_check_run_for_another_constraint_leaves_constraint_unverified(tmp_path: Path) -> None:
    project = _project(tmp_path)
    constraint = _constraint(project)
    _run(project, "someone-else", "pass")

    results = constraint_outcomes(project.records(), [constraint["id"]], HEAD)

    assert results == [ConstraintResult("unverified", constraint["id"], HEAD)]


def test_version_is_the_superseding_record_id_and_old_evidence_does_not_carry(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    old = _constraint(project)
    _run(project, old["id"], "pass")
    new = project.supersede(
        old["id"],
        payload={
            "area": "payments",
            "rule": "Only payments adapters import Stripe.",
            "check": "true",
        },
        body="## Basis\n\nProvider access belongs in billing adapters.\n",
    )["record"]

    results = constraint_outcomes(project.records(), [old["id"], new["id"]], HEAD)

    assert results == [
        ConstraintResult("verified", old["id"], HEAD),
        ConstraintResult("unverified", new["id"], HEAD),
    ]


def test_each_result_carries_the_queried_revision(tmp_path: Path) -> None:
    project = _project(tmp_path)
    first = _constraint(project)
    second = _constraint(project, "second-constraint")
    _run(project, first["id"], "pass", revision=OTHER_HEAD)
    _run(project, second["id"], "fail", revision=HEAD)

    results = constraint_outcomes(project.records(), [first["id"], second["id"]], OTHER_HEAD)

    assert [(r.constraint_id, r.outcome, r.revision) for r in results] == [
        (first["id"], "verified", OTHER_HEAD),
        (second["id"], "unverified", OTHER_HEAD),
    ]


def test_check_run_that_is_neither_pass_nor_fail_is_inconclusive(tmp_path: Path) -> None:
    project = _project(tmp_path)
    constraint = _constraint(project)
    _run(project, constraint["id"], "blocked")

    results = constraint_outcomes(project.records(), [constraint["id"]], HEAD)

    assert results == [ConstraintResult("inconclusive", constraint["id"], HEAD)]
