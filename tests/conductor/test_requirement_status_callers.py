from __future__ import annotations

import itertools
from pathlib import Path

from canon_support import create
from test_task_land import _evidence_file, _git
from test_task_land_close import _world
from test_task_landing_operation import _make_closing_task, _tree

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.phases.progress import phase_progress
from orchestra.conductor.tasks import verification
from orchestra.conductor.tasks.land_task import LandedTask
from orchestra.conductor.tasks.task_landing import land_and_close
from orchestra.conductor.verification.requirements import release_ready, requirement_status

OLD_REVISION = "0" * 40


def _add_stale_pass(project: Project) -> None:
    create(
        project,
        "score:acceptance",
        "b",
        {
            "method": "check",
            "phase": "ph",
            "effort": "ef",
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    acceptance = project.resolve("score:acceptance", "b")
    create(
        project,
        "tuner:check-run",
        "b",
        {
            "criterion_id": acceptance["id"],
            "effort": "ef",
            "method": "check",
            "result": "pass",
            "revision": OLD_REVISION,
            "signed_by": "",
        },
    )


def test_task_close_stale_head_pass_leaves_requirement_unverified(tmp_path: Path) -> None:
    project, repo = _world(tmp_path)
    _add_stale_pass(project)
    landing = land_and_close(project, repo, "a", _evidence_file(tmp_path))
    assert landing.closure.state == "in_progress"
    assert landing.closure.reasons == ("requirements not verified: R1",)


def test_requirement_status_stale_head_pass_is_unverified_at_the_head(tmp_path: Path) -> None:
    project, _ = _world(tmp_path)
    _add_stale_pass(project)
    head = _git(_tree(project), "rev-parse", "HEAD")
    records = project.records()
    assert requirement_status(records, "ph", OLD_REVISION)["R1"].status == "unverified"
    assert requirement_status(records, "ph", head)["R1"].status == "unverified"
    assert not release_ready(records, "ph", head)


def test_closing_verification_stale_head_pass_leaves_requirement_unverified(
    tmp_path: Path,
) -> None:
    project, _ = _world(tmp_path)
    _make_closing_task(project)
    _add_stale_pass(project)
    tree = _tree(project)
    landed = LandedTask(
        task="a",
        phase="ph",
        commit="",
        revision=_git(tree, "rev-parse", "HEAD"),
        report_id="",
        checks=(),
        evidence_result="pass",
        verdict="pass",
    )
    run = verification.run_closing_checks(project, landed)
    assert run.refusal == ""
    assert "R1" not in run.verified


_CLOCK = itertools.count()
HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"


def _record(record_type: str, subject: str, payload: JsonObject, state: str = "active") -> Record:
    n = next(_CLOCK)
    return {
        "id": f"<{record_type}:{subject}-{n}>",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": f"r{n}",
        "recorded_at": f"2026-11-01T00:00:{n:02d}Z",
        "derived": {"write_order": n},
    }


def _phase_records(method: str = "check") -> tuple[list[Record], Record]:
    phase = _record("score:phase", "p", {"title": "p", "ordinal": 1, "effort": "e"}, "done")
    spec = _record("score:specification", "p", {"phase": "p", "requirements": ["R1"]}, "active")
    acceptance = _record(
        "score:acceptance",
        "a1",
        {
            "phase": "p",
            "effort": "e",
            "requirement": "R1",
            "method": method,
            "verify_command": "true",
        },
    )
    return [phase, spec, acceptance], acceptance


def _pass_at(acceptance: Record, revision: str, signed_by: str = "") -> Record:
    return _record(
        "tuner:check-run",
        "a1",
        {
            "criterion_id": acceptance["id"],
            "result": "pass",
            "revision": revision,
            "signed_by": signed_by,
        },
        "recorded",
    )


def _ready(records: list[Record], head: str | None = None) -> tuple[bool, str]:
    readiness = phase_progress.verification_readiness(
        phase_progress.acceptance_holds(records, "p", head), "not-required"
    )
    return readiness.ready, readiness.reason


def test_workflow_readiness_stale_head_pass_is_not_ready() -> None:
    records, acceptance = _phase_records()
    records.append(_pass_at(acceptance, OLD_REVISION))
    ready, reason = _ready(records, HEAD)
    assert not ready
    assert "R1" in reason
    assert _ready(records) == (True, "")


def test_workflow_readiness_holds_with_a_pass_at_the_head() -> None:
    records, acceptance = _phase_records()
    records.append(_pass_at(acceptance, OLD_REVISION))
    records.append(_pass_at(acceptance, HEAD))
    assert _ready(records, HEAD) == (True, "")


def test_workflow_readiness_unsigned_manual_pass_is_not_ready() -> None:
    records, acceptance = _phase_records("manual")
    records.append(_pass_at(acceptance, HEAD))
    assert not _ready(records)[0]
    records.append(_pass_at(acceptance, HEAD, signed_by="alice"))
    assert _ready(records) == (True, "")
