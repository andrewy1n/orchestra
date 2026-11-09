"""Tests for the Landing head commit (R7)."""

from __future__ import annotations

import sys
from pathlib import Path

from conftest import REPO_ROOT, git, make_git_repo

sys.path.insert(0, str(REPO_ROOT))
from dashboard.backend.landing import Landing, phase_landing

BODY = """\
## Landing

- Branch: `phase/cards`
- Base: `main`
"""


def _scratch_main() -> Path:
    root = make_git_repo()
    git(root, "branch", "-M", "main")
    return root


def _commit(root: Path, name: str) -> None:
    (root / name).write_text(name)
    git(root, "add", name)
    git(root, "commit", "-qm", name)


def _tip(root: Path, ref: str) -> str:
    return git(root, "rev-parse", ref).stdout.strip()


def _phase_branch(root: Path, commits: int) -> None:
    git(root, "checkout", "-qb", "phase/cards")
    for index in range(commits):
        _commit(root, f"f{index}.txt")
    git(root, "checkout", "-q", "main")


def test_r7_head_is_the_phase_branch_tip():
    root = _scratch_main()
    _phase_branch(root, 2)

    result = phase_landing(root, BODY, "cards")

    assert result is not None
    assert result.head == _tip(root, "phase/cards")
    assert len(result.head) == 40


def test_r7_head_follows_the_branch_when_it_advances():
    root = _scratch_main()
    _phase_branch(root, 1)
    first = phase_landing(root, BODY, "cards")
    git(root, "checkout", "-q", "phase/cards")
    _commit(root, "later.txt")
    git(root, "checkout", "-q", "main")

    second = phase_landing(root, BODY, "cards")

    assert first is not None and second is not None
    assert second.head != first.head
    assert second.head == _tip(root, "phase/cards")


def test_r7_head_is_empty_when_the_branch_does_not_exist():
    root = _scratch_main()

    result = phase_landing(root, BODY, "cards")

    assert result is not None
    assert result.exists is False
    assert result.head == ""


def test_r7_head_defaults_to_empty_on_a_constructed_landing():
    landing = Landing(branch="phase/cards", exists=False, ahead=0, merged=False)

    assert landing.head == ""


def test_r7_existing_fields_keep_their_values_for_an_unmerged_branch():
    root = _scratch_main()
    _phase_branch(root, 2)

    result = phase_landing(root, BODY, "cards")

    assert result is not None
    assert (result.branch, result.exists, result.ahead, result.merged) == (
        "phase/cards",
        True,
        2,
        False,
    )


def test_r7_existing_fields_keep_their_values_for_a_merged_branch():
    root = _scratch_main()
    _phase_branch(root, 1)
    git(root, "merge", "-q", "--no-ff", "phase/cards", "-m", "merge landing")

    result = phase_landing(root, BODY, "cards")

    assert result is not None
    assert (result.branch, result.exists, result.ahead, result.merged) == (
        "phase/cards",
        True,
        0,
        True,
    )
    assert result.head == _tip(root, "phase/cards")


def test_r7_existing_fields_keep_their_values_for_a_missing_branch():
    root = _scratch_main()

    result = phase_landing(root, BODY, "cards")

    assert result is not None
    assert (result.branch, result.exists, result.ahead, result.merged) == (
        "phase/cards",
        False,
        0,
        False,
    )
