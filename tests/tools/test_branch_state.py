from __future__ import annotations

from pathlib import Path

import pytest

from orchestra.tools import Absent, Git, Merged, ReadFailed, Unmerged, branch_state


def _commit(git: Git, message: str) -> str:
    git.text("add", "-A")
    git.text("-c", "commit.gpgsign=false", "commit", "-m", message)
    return git.head()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git = Git(root)
    git.text("init", "-b", "main")
    git.text("config", "user.name", "Test")
    git.text("config", "user.email", "test@example.com")
    (root / "base.txt").write_text("base\n")
    _commit(git, "base")
    return root


def test_branch_state_merged_when_branch_has_no_unique_commits(repo: Path) -> None:
    git = Git(repo)
    git.create_branch("phase/x", "main")

    assert branch_state(repo, "phase/x") == Merged(head=git.head())


def test_branch_state_merged_when_tip_is_patch_equivalent_to_main(repo: Path) -> None:
    git = Git(repo)
    git.create_branch("phase/x", "main")
    git.text("checkout", "phase/x")
    (repo / "feature.txt").write_text("feature\n")
    tip = _commit(git, "feature")
    git.text("checkout", "main")
    git.text("cherry-pick", tip)

    assert branch_state(repo, "phase/x") == Merged(head=tip)


def test_branch_state_unmerged_counts_unique_commits(repo: Path) -> None:
    git = Git(repo)
    git.create_branch("phase/x", "main")
    git.text("checkout", "phase/x")
    (repo / "a.txt").write_text("one\n")
    _commit(git, "one")
    (repo / "a.txt").write_text("two\n")
    tip = _commit(git, "two")
    git.text("checkout", "main")

    assert branch_state(repo, "phase/x") == Unmerged(head=tip, ahead=2)


def test_branch_state_absent_when_branch_does_not_exist(repo: Path) -> None:
    assert branch_state(repo, "phase/missing") == Absent()


def test_branch_state_read_failed_outside_a_repository(tmp_path: Path) -> None:
    result = branch_state(tmp_path, "phase/x")

    assert isinstance(result, ReadFailed)
    assert "not a git repository" in result.reason


def test_branch_state_read_failed_for_broken_ref(repo: Path) -> None:
    (repo / ".git" / "refs" / "heads" / "phase-broken").write_text("garbage\n")

    result = branch_state(repo, "phase-broken")

    assert isinstance(result, ReadFailed)
    assert "broken ref" in result.reason


def test_branch_state_read_failed_when_ref_points_at_missing_object(repo: Path) -> None:
    (repo / ".git" / "refs" / "heads" / "phase-dangling").write_text("1" * 40 + "\n")

    assert isinstance(branch_state(repo, "phase-dangling"), ReadFailed)


def test_branch_state_read_failed_when_base_is_missing(repo: Path) -> None:
    Git(repo).create_branch("phase/x", "main")

    result = branch_state(repo, "phase/x", base="no-such-base")

    assert isinstance(result, ReadFailed)
    assert "no-such-base" in result.reason


def test_branch_state_read_failed_when_git_is_not_runnable(
    repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))

    assert isinstance(branch_state(repo, "phase/x"), ReadFailed)
