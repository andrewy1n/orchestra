"""The descent term keeps a review valid across a clean merge of the Landing base."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import git, make_git_repo

from orchestra.conductor.landing import gate


def _commit(repo: Path, path: str, text: str, message: str) -> None:
    (repo / path).write_text(text)
    assert git(repo, "add", path).returncode == 0
    assert git(repo, "commit", "-qm", message).returncode == 0


def _rev(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def repo() -> Path:
    root = make_git_repo()
    git(root, "branch", "-M", "main")
    _commit(root, "shared.txt", "one\n", "shared")
    _commit(root, "conflict.txt", "start\n", "conflict")
    git(root, "switch", "-qc", "phase")
    _commit(root, "phase.txt", "phase\n", "phase work")
    return root


def _advance_base(repo: Path, path: str, text: str) -> None:
    git(repo, "switch", "-q", "main")
    _commit(repo, path, text, f"base {path}")
    git(repo, "switch", "-q", "phase")


def test_clean_base_merge_keeps_review_valid(repo: Path) -> None:
    reviewed = _rev(repo)
    _advance_base(repo, "shared.txt", "two\n")
    assert git(repo, "merge", "-q", "--no-ff", "-m", "merge main", "main").returncode == 0

    term = gate._descent_term(repo, reviewed, base="main")

    assert term.holds, term.detail


def test_clean_base_merge_with_canon_change_keeps_review_valid(repo: Path) -> None:
    reviewed = _rev(repo)
    _advance_base(repo, "shared.txt", "two\n")
    git(repo, "merge", "-q", "--no-ff", "-m", "merge main", "main")
    (repo / ".canon").mkdir()
    _commit(repo, ".canon/log.jsonl", "{}\n", "canon")

    assert gate._descent_term(repo, reviewed, base="main").holds


def test_phase_edit_after_base_merge_requires_review(repo: Path) -> None:
    reviewed = _rev(repo)
    _advance_base(repo, "shared.txt", "two\n")
    git(repo, "merge", "-q", "--no-ff", "-m", "merge main", "main")
    _commit(repo, "phase.txt", "edited\n", "phase edit")

    term = gate._descent_term(repo, reviewed, base="main")

    assert not term.holds
    assert "phase.txt" in term.detail
    assert "shared.txt" not in term.detail


def test_phase_edit_without_merge_requires_review(repo: Path) -> None:
    reviewed = _rev(repo)
    _commit(repo, "phase.txt", "edited\n", "phase edit")

    term = gate._descent_term(repo, reviewed, base="main")

    assert not term.holds
    assert "phase.txt" in term.detail


def test_conflict_resolution_requires_review(repo: Path) -> None:
    _commit(repo, "conflict.txt", "phase side\n", "phase conflict")
    reviewed = _rev(repo)
    _advance_base(repo, "conflict.txt", "base side\n")
    assert git(repo, "merge", "-q", "main").returncode != 0
    (repo / "conflict.txt").write_text("resolved\n")
    git(repo, "add", "conflict.txt")
    assert git(repo, "commit", "-qm", "merge main").returncode == 0

    term = gate._descent_term(repo, reviewed, base="main")

    assert not term.holds
    assert "conflict.txt" in term.detail
