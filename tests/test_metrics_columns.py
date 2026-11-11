from __future__ import annotations

from pathlib import Path

from canon_support import create
from test_metrics_phases import _phase, _row, _world

from orchestra.canon.project import Project, open_store
from orchestra.metrics.ops import count_operations
from orchestra.metrics.phases import build_phase_rows


def _acceptance(project: Project, phase: str, name: str) -> None:
    create(
        project,
        "score:acceptance",
        name,
        {
            "phase": phase,
            "requirement": "R1",
            "method": "check",
            "effort": "ef",
            "verify_command": "true",
        },
    )


def _run(project: Project, subject: str, result: str, method: str = "check") -> None:
    create(
        project,
        "tuner:check-run",
        subject,
        {
            "criterion_id": subject,
            "revision": "abc",
            "result": result,
            "effort": "ef",
            "method": method,
            "signed_by": "",
        },
        "ok",
    )


def _repair(project: Project, cause: str, phase: str | None, fix: str) -> None:
    payload: dict = {"fix": fix, "cause": cause}
    if phase is not None:
        payload["phase"] = phase
    create(project, "conductor:repair-link", f"repair-{fix}", payload)


def _review(project: Project, phase: str, authority: str, name: str) -> None:
    create(
        project,
        "score:step-review",
        name,
        {
            "effort": "ef",
            "phase": phase,
            "step": "spec",
            "reviewed_artifact": project.records()[0]["id"],
            "reviewed_revision": "r",
            "input_fingerprint": "f",
            "source_reviews": [],
            "authority": authority,
            "basis": "b",
        },
    )


def test_review_rounds_count_review_check_runs_of_the_phase(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    _phase(project, "ph-b", "ef")
    _run(project, "ph-a-r1", "fail", "review")
    _run(project, "ph-a-r2", "pass", "review")
    _run(project, "ph-a-c1", "pass", "check")
    _run(project, "ph-b-r1", "pass", "review")
    rows = build_phase_rows(tmp_path)
    assert _row(rows, "ph-a").review_rounds == 2
    assert _row(rows, "ph-b").review_rounds == 1


def test_review_rounds_are_zero_without_review_check_runs(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    _run(project, "ph-a-c1", "pass", "check")
    assert _row(build_phase_rows(tmp_path), "ph-a").review_rounds == 0


def test_failed_check_runs_count_fail_results_of_the_phase(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    _phase(project, "ph-b", "ef")
    _run(project, "ph-a-c1", "fail")
    _run(project, "ph-a-c2", "fail")
    _run(project, "ph-a-c3", "pass")
    _run(project, "ph-a-c4", "blocked")
    _run(project, "ph-b-c1", "fail")
    rows = build_phase_rows(tmp_path)
    assert _row(rows, "ph-a").failed_check_runs == 2
    assert _row(rows, "ph-b").failed_check_runs == 1


def test_failed_check_runs_match_criteria_of_phase_acceptances(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    acceptance = create(
        project,
        "score:acceptance",
        "crit-x",
        {
            "phase": "ph-a",
            "requirement": "R1",
            "method": "check",
            "effort": "ef",
            "verify_command": "true",
        },
    )
    _run(project, acceptance["id"], "fail")
    assert _row(build_phase_rows(tmp_path), "ph-a").failed_check_runs == 1


def test_human_decisions_count_answers_user_approvals_and_amendments(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    _acceptance(project, "ph-a", "ph-a-acc")
    question = create(
        project,
        "score:continuity-question",
        "q1",
        {"owner": "u", "blocking": True, "scope": "s", "phase": "ph-a"},
    )
    project.update(
        question["id"], record_type="score:continuity-question", payload={"answer": "yes"}
    )
    create(
        project,
        "score:continuity-question",
        "q2",
        {"owner": "u", "blocking": True, "scope": "s", "phase": "ph-a"},
    )
    _review(project, "ph-a", "user-approval", "sr1")
    _review(project, "ph-a", "explicit-delegation", "sr2")
    create(
        project,
        "tuner:oracle-amendment",
        "am1",
        {
            "acceptance": "ph-a-acc",
            "effort": "ef",
            "phase": "ph-a",
            "old_hashes": [],
            "new_hashes": [],
            "status": "approved",
        },
    )
    assert _row(build_phase_rows(tmp_path), "ph-a").human_decisions == 3


def test_human_decisions_are_zero_without_human_records(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    assert _row(build_phase_rows(tmp_path), "ph-a").human_decisions == 0


def test_repairs_by_cause_count_repair_links_naming_the_phase(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    _phase(project, "ph-b", "ef")
    _repair(project, "spec-gap", "ph-a", "f1")
    _repair(project, "spec-gap", "ph-a", "f2")
    _repair(project, "verification-miss", "ph-a", "f3")
    _repair(project, "spec-gap", "ph-b", "f4")
    _repair(project, "no-phase", None, "f5")
    rows = build_phase_rows(tmp_path)
    assert _row(rows, "ph-a").repairs_by_cause == {"spec-gap": 2, "verification-miss": 1}
    assert _row(rows, "ph-b").repairs_by_cause == {"spec-gap": 1}


def test_repairs_by_cause_is_empty_without_repair_links(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef")
    assert _row(build_phase_rows(tmp_path), "ph-a").repairs_by_cause == {}


def test_operations_per_task_equals_operations_over_tasks(tmp_path: Path) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef", tasks=2)
    counts, tasks = count_operations(open_store(tmp_path, read_only=True), "ph-a")
    row = _row(build_phase_rows(tmp_path), "ph-a")
    assert tasks == 2
    assert row.operations_per_task == sum(counts.values()) / tasks


def test_operations_per_task_is_null_with_reason_when_the_phase_has_no_tasks(
    tmp_path: Path,
) -> None:
    project = _world(tmp_path)
    _phase(project, "ph-a", "ef", tasks=0)
    row = _row(build_phase_rows(tmp_path), "ph-a")
    assert row.operations_per_task is None
    assert row.missing["operations_per_task"]
