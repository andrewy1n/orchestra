from __future__ import annotations

from pathlib import Path

import pytest
from test_task_land import PHASE, _evidence_file, _git, _world

from orchestra.canon.project import Project
from orchestra.conductor.tasks.close import task_close
from orchestra.conductor.tasks.task_landing import TaskLanding, land_and_close


class _CloseFailed(RuntimeError):
    pass


def _gated_world(tmp_path: Path) -> tuple[Project, Path, Path, Path]:
    gate = tmp_path / "gate"
    project, repo, tree = _world(tmp_path, verify_command=f"test -f {gate}")
    return project, repo, tree, gate


def _fail_next_close(monkeypatch: pytest.MonkeyPatch) -> None:
    real = task_close.close
    calls: list[int] = []

    def close(*args: object, **kwargs: object) -> task_close.Closure:
        calls.append(1)
        if len(calls) == 1:
            raise _CloseFailed("closure failed after landing")
        return real(*args, **kwargs)  # pyright: ignore[reportArgumentType]

    monkeypatch.setattr(task_close, "close", close)


def _land(project: Project, repo: Path, tmp_path: Path) -> TaskLanding:
    return land_and_close(project, repo, "a", _evidence_file(tmp_path))


def _land_then_retry_after_failed_close(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[Project, Path, TaskLanding, str]:
    project, repo, tree = _world(tmp_path)
    (tree / "work.txt").write_text("work\n")
    _fail_next_close(monkeypatch)
    with pytest.raises(_CloseFailed):
        _land(project, repo, tmp_path)
    first_head = _git(tree, "rev-parse", "HEAD")
    return project, tree, _land(project, repo, tmp_path), first_head


def _task_commits(tree: Path) -> list[str]:
    return _git(tree, "rev-list", f"phase/{PHASE}..HEAD").split()


def test_r9_a_retry_after_a_failed_close_creates_no_new_task_commit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _, tree, retry, first_head = _land_then_retry_after_failed_close(monkeypatch, tmp_path)
    assert retry.landed.commit == ""
    assert _git(tree, "rev-parse", "HEAD") == first_head
    assert _task_commits(tree) == [first_head]


def test_r9_a_retry_after_a_failed_check_creates_no_new_task_commit(tmp_path: Path) -> None:
    project, repo, tree, gate = _gated_world(tmp_path)
    (tree / "work.txt").write_text("work\n")
    first = _land(project, repo, tmp_path)
    assert first.closure.state == "in_progress"
    gate.write_text("ok\n")
    retry = _land(project, repo, tmp_path)
    assert retry.landed.commit == ""
    assert retry.landed.revision == first.landed.revision
    assert _task_commits(tree) == [first.landed.commit]


def test_r10_a_retry_after_a_failed_close_reuses_the_first_execution_report(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project, _, retry, _ = _land_then_retry_after_failed_close(monkeypatch, tmp_path)
    reports = project.list("conductor:execution-report")
    assert [r["id"] for r in reports] == [retry.landed.report_id]


def test_r10_a_retry_after_a_failed_check_reuses_the_first_execution_report(
    tmp_path: Path,
) -> None:
    project, repo, tree, gate = _gated_world(tmp_path)
    (tree / "work.txt").write_text("work\n")
    first = _land(project, repo, tmp_path)
    gate.write_text("ok\n")
    retry = _land(project, repo, tmp_path)
    assert retry.landed.report_id == first.landed.report_id
    assert len(project.list("conductor:execution-report")) == 1


def test_r11_a_retry_after_a_failed_close_reruns_the_checks_at_the_same_revision(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    counter = tmp_path / "runs"
    project, repo, tree = _world(tmp_path, verify_command=f"echo run >> {counter}")
    (tree / "work.txt").write_text("work\n")
    _fail_next_close(monkeypatch)
    with pytest.raises(_CloseFailed):
        _land(project, repo, tmp_path)
    first_head = _git(tree, "rev-parse", "HEAD")
    retry = _land(project, repo, tmp_path)
    assert counter.read_text().split() == ["run", "run"]
    assert retry.landed.revision == first_head
    runs = project.list("tuner:check-run")
    assert {str(r["payload"]["revision"]) for r in runs} == {first_head}
    assert retry.landed.checks[0].check_run_id in {r["id"] for r in runs}


def test_r11_a_retry_after_a_failed_check_records_a_new_passing_run(tmp_path: Path) -> None:
    project, repo, tree, gate = _gated_world(tmp_path)
    (tree / "work.txt").write_text("work\n")
    first = _land(project, repo, tmp_path)
    gate.write_text("ok\n")
    retry = _land(project, repo, tmp_path)
    runs = project.list("tuner:check-run")
    assert sorted(str(r["payload"]["result"]) for r in runs) == ["fail", "pass"]
    assert {str(r["payload"]["revision"]) for r in runs} == {first.landed.revision}
    passing = next(r for r in runs if r["payload"]["result"] == "pass")
    assert retry.landed.checks[0].check_run_id == passing["id"]


def test_r12_a_closure_after_a_new_commit_ignores_check_runs_of_the_earlier_revision(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project, repo, tree, gate = _gated_world(tmp_path)
    gate.write_text("ok\n")
    (tree / "work.txt").write_text("work\n")
    _fail_next_close(monkeypatch)
    with pytest.raises(_CloseFailed):
        _land(project, repo, tmp_path)
    gate.unlink()
    (tree / "more.txt").write_text("more\n")
    second = _land(project, repo, tmp_path)
    assert second.closure.state == "in_progress"
    assert second.closure.reasons
    assert project.resolve("score:work-item", "a")["lifecycle_state"] == "in_progress"


def test_r12_the_closure_decision_reads_only_check_runs_of_the_landing_revision(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project, repo, tree = _world(tmp_path)
    (tree / "work.txt").write_text("work\n")
    _fail_next_close(monkeypatch)
    with pytest.raises(_CloseFailed):
        _land(project, repo, tmp_path)
    (tree / "more.txt").write_text("more\n")
    seen: list[list[str]] = []
    real = task_close.decide_close

    def spy(
        asked: Project, criteria: list[task_close.CriterionRequest], **kwargs: object
    ) -> task_close.CloseDecision:
        seen.append([c["check_run_id"] for c in criteria])
        return real(asked, criteria, **kwargs)  # pyright: ignore[reportArgumentType]

    monkeypatch.setattr(task_close, "decide_close", spy)
    second = _land(project, repo, tmp_path)
    head = _git(tree, "rev-parse", "HEAD")
    assert second.landed.revision == head
    assert second.closure.state == "done"
    stored = [project.get(i, "tuner:check-run") for i in seen[0]]
    assert [r["payload"]["revision"] for r in stored] == [head]
    report = project.get(second.landed.report_id, "conductor:execution-report")
    assert report["payload"]["revision"] == head
    assert len(project.list("conductor:execution-report")) == 2
