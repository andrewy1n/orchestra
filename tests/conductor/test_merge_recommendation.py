from __future__ import annotations

import json
from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra.canon.project import Project
from orchestra.cli import main
from orchestra.conductor.github_evidence import GitHubActionsAdapter
from orchestra.conductor.merge_evidence import (
    CheckEvidence,
    CheckState,
    EvidenceRequest,
    EvidenceSnapshot,
    RequiredCheck,
)
from orchestra.tools import Git, ToolError

URL = "https://github.com/owner/repo/pull/7"
RUN = f"{URL.split('/pull')[0]}/actions/runs/42"
REQUIRED = RequiredCheck("test", "42")


@pytest.fixture
def project(tmp_path: Path) -> Project:
    project = make_project(tmp_path / "repo")
    seed_effort(project)
    root = project.project_root
    config = root / "orchestra.toml"
    with config.open("a", encoding="utf-8") as file:
        file.write('\n[merge_evidence]\nadapter = "github-actions"\n')
    git = Git(root)
    git.run("add", "orchestra.toml")
    git.run("commit", "-qm", "Configure CI evidence")
    head = git.head()
    tasks = (
        ("build", []),
        ("verify-phase", ["build"]),
    )
    for task, dependencies in tasks:
        row = create(
            project,
            "score:work-item",
            task,
            {
                "title": task,
                "kind": "deliver",
                "assignee": "",
                "phase": "p1",
                "effort": "alpha",
                "depends_on": dependencies,
            },
        )
        project.update(row["id"], transition="in_progress")
        project.update(row["id"], transition="done")
    create(
        project,
        "conductor:landing",
        "p1",
        {
            "phase": "p1",
            "effort": "alpha",
            "number": 7,
            "url": URL,
            "head_sha": head,
            "result": "success",
        },
    )
    create(
        project,
        "conductor:proof-packet",
        "p1",
        {
            "phase": "p1",
            "effort": "alpha",
            "revision": head,
            "base": head,
            "kind": "commands",
        },
    )
    create(
        project,
        "tuner:check-run",
        "p1-review",
        {
            "criterion_id": "p1-review",
            "effort": "alpha",
            "revision": head,
            "result": "pass",
            "method": "review",
            "signed_by": "",
        },
    )
    git.run("worktree", "add", "-q", "--detach", ".worktrees/p1", head)
    return project


def _invoke(project: Project, expected_exit: int) -> None:
    try:
        result = main(["merge-evidence", "--phase", "p1", "--cwd", str(project.project_root)])
    except SystemExit as error:
        result = error.code
    assert result == expected_exit, f"expected merge evidence exit {expected_exit}, got {result}"


def test_refresh_reports_pending_failure_rerun_and_new_head(
    project: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    head = Git(project.project_root).head()
    states: tuple[tuple[str, CheckState, str, int], ...] = (
        (head, "pending", "unresolved", 1),
        (head, "fail", "blocked", 1),
        (head, "pass", "ready", 0),
        ("a" * 40, "pass", "unresolved", 1),
    )
    snapshots = iter(
        EvidenceSnapshot(remote_head, (REQUIRED,), (CheckEvidence(REQUIRED, state, head, RUN),))
        for remote_head, state, _, _ in states
    )

    def read(_self: GitHubActionsAdapter, request: EvidenceRequest) -> EvidenceSnapshot:
        assert request.pull_request_url == URL
        return next(snapshots)

    monkeypatch.setattr(GitHubActionsAdapter, "read", read)
    for remote_head, state, recommendation, expected_exit in states:
        _invoke(project, expected_exit)
        output = json.loads(capsys.readouterr().out)
        assert output["recommendation"] == recommendation
        assert output["head"] == remote_head
        assert output["phase_verification"] == ("pass" if remote_head == head else "blocked")
        assert output["checks"][0]["run_url"] == RUN
        assert output["checks"][0]["state"] == state
    observations = project.list("conductor:ci-observation")
    assert len(observations) == 4
    assert all(row["payload"]["provider"] == "github-actions" for row in observations)


def test_lookup_failure_does_not_reuse_previous_passing_ci(
    project: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    head = Git(project.project_root).head()

    snapshots = iter(
        (
            EvidenceSnapshot(head, (REQUIRED,), (CheckEvidence(REQUIRED, "pass", head, RUN),)),
            EvidenceSnapshot(head, unresolved="rules unavailable"),
        )
    )

    def read(_self: GitHubActionsAdapter, request: EvidenceRequest) -> EvidenceSnapshot:
        return next(snapshots)

    monkeypatch.setattr(GitHubActionsAdapter, "read", read)
    _invoke(project, 0)
    capsys.readouterr()
    _invoke(project, 1)
    output = json.loads(capsys.readouterr().out)
    assert output["recommendation"] == "unresolved"
    assert output["phase_verification"] == "pass"
    assert "rules unavailable" in output["blockers"]


def test_phase_review_failure_blocks_ready_with_passing_ci(
    project: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    head = Git(project.project_root).head()
    review = project.resolve("tuner:check-run", "p1-review")
    project.correct(review["id"], payload={"result": "fail"})

    def read(_self: GitHubActionsAdapter, request: EvidenceRequest) -> EvidenceSnapshot:
        return EvidenceSnapshot(head, (REQUIRED,), (CheckEvidence(REQUIRED, "pass", head, RUN),))

    monkeypatch.setattr(GitHubActionsAdapter, "read", read)
    _invoke(project, 1)
    output = json.loads(capsys.readouterr().out)
    assert output["recommendation"] == "blocked"
    assert any("review-at-head" in reason for reason in output["blockers"])


def test_missing_required_result_leaves_mixed_evidence_unresolved(
    project: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    head = Git(project.project_root).head()
    missing = RequiredCheck("package")

    def read(_self: GitHubActionsAdapter, request: EvidenceRequest) -> EvidenceSnapshot:
        return EvidenceSnapshot(
            head, (REQUIRED, missing), (CheckEvidence(REQUIRED, "fail", head, RUN),)
        )

    monkeypatch.setattr(GitHubActionsAdapter, "read", read)
    _invoke(project, 1)
    output = json.loads(capsys.readouterr().out)
    assert output["recommendation"] == "unresolved"
    assert any("required CI check failed" in reason for reason in output["blockers"])
    assert any("required CI result is missing" in reason for reason in output["blockers"])


def test_no_required_checks_leaves_verified_phase_unresolved(
    project: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    head = Git(project.project_root).head()
    monkeypatch.setattr(GitHubActionsAdapter, "read", lambda *_: EvidenceSnapshot(head))

    _invoke(project, 1)

    output = json.loads(capsys.readouterr().out)
    assert output["phase_verification"] == "pass"
    assert output["recommendation"] == "unresolved"
    assert output["blockers"] == ["no required CI checks are configured"]


def test_unknown_adapter_exits_without_recording_an_observation(
    project: Project, capsys: pytest.CaptureFixture[str]
) -> None:
    config = project.project_root / ".worktrees/p1/orchestra.toml"
    config.write_text(config.read_text().replace('"github-actions"', '"unknown-ci"'))

    _invoke(project, 2)

    captured = capsys.readouterr()
    assert "unknown-ci" in captured.err
    assert not captured.out
    assert not project.list("conductor:ci-observation")


def test_missing_phase_worktree_exits_without_recording_an_observation(
    project: Project, capsys: pytest.CaptureFixture[str]
) -> None:
    Git(project.project_root).run("worktree", "remove", ".worktrees/p1")

    _invoke(project, 2)

    assert "phase worktree" in capsys.readouterr().err
    assert not project.list("conductor:ci-observation")


def test_unreadable_worktree_head_exits_without_recording_an_observation(
    project: Project, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    head = Git(project.project_root).head()
    monkeypatch.setattr(GitHubActionsAdapter, "read", lambda *_: EvidenceSnapshot(head))

    def read_head(_self: Git) -> str:
        raise ToolError("cannot read worktree HEAD", ("git", "rev-parse", "HEAD"), 128, "")

    monkeypatch.setattr(Git, "head", read_head)

    _invoke(project, 2)

    assert "cannot read worktree HEAD" in capsys.readouterr().err
    assert not project.list("conductor:ci-observation")
