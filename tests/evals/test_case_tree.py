from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from evals.seeded_defects.trees import PatchDoesNotApply, build_case_tree


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


@dataclass
class SourceRepo:
    path: Path
    base: str
    landing: str
    later: str


@pytest.fixture
def source(tmp_path: Path) -> SourceRepo:
    path = tmp_path / "source"
    path.mkdir()
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "user.email", "t@example.com")
    git(path, "config", "user.name", "t")
    (path / "a.txt").write_text("one\ntwo\nthree\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "base")
    base = git(path, "rev-parse", "HEAD")
    (path / "a.txt").write_text("one\ntwo\nthree\nfour\n")
    (path / "b.txt").write_text("landed\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "landing")
    landing = git(path, "rev-parse", "HEAD")
    (path / "c.txt").write_text("later\n")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "later")
    later = git(path, "rev-parse", "HEAD")
    git(path, "tag", "v-landing", landing)
    git(path, "branch", "side", landing)
    return SourceRepo(path, base, landing, later)


@pytest.fixture
def defect_patch(tmp_path: Path) -> Path:
    patch = tmp_path / "defect.patch"
    patch.write_text(
        "diff --git a/a.txt b/a.txt\n"
        "--- a/a.txt\n"
        "+++ b/a.txt\n"
        "@@ -1,4 +1,4 @@\n"
        " one\n"
        "-two\n"
        "+TWO\n"
        " three\n"
        " four\n"
    )
    return patch


@pytest.fixture
def bad_patch(tmp_path: Path) -> Path:
    patch = tmp_path / "bad.patch"
    patch.write_text(
        "diff --git a/a.txt b/a.txt\n"
        "--- a/a.txt\n"
        "+++ b/a.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " nothing\n"
        "-matches\n"
        "+here\n"
        " at all\n"
    )
    return patch


def test_tree_holds_landed_change_and_defect_patch(
    source: SourceRepo, defect_patch: Path, tmp_path: Path
) -> None:
    dest = tmp_path / "tree"
    build_case_tree(source.path, source.landing, defect_patch, dest)
    assert (dest / "a.txt").read_text() == "one\nTWO\nthree\nfour\n"
    assert (dest / "b.txt").read_text() == "landed\n"


def test_tree_has_one_commit_on_top_of_landing_parent(
    source: SourceRepo, defect_patch: Path, tmp_path: Path
) -> None:
    dest = tmp_path / "tree"
    build_case_tree(source.path, source.landing, defect_patch, dest)
    assert git(dest, "rev-list", "--count", "HEAD") == "2"
    assert git(dest, "rev-parse", "HEAD~1") == source.base


def test_tree_excludes_later_history(
    source: SourceRepo, defect_patch: Path, tmp_path: Path
) -> None:
    dest = tmp_path / "tree"
    build_case_tree(source.path, source.landing, defect_patch, dest)
    assert not (dest / "c.txt").exists()


def test_tree_has_no_ref_to_landing_or_later_history(
    source: SourceRepo, defect_patch: Path, tmp_path: Path
) -> None:
    dest = tmp_path / "tree"
    build_case_tree(source.path, source.landing, defect_patch, dest)
    refs = git(dest, "for-each-ref", "--format=%(refname) %(objectname)")
    assert source.landing not in refs
    assert source.later not in refs
    assert "refs/remotes" not in refs
    assert "refs/tags" not in refs
    assert "refs/heads/side" not in refs


def test_tree_head_is_not_the_landing_commit(
    source: SourceRepo, defect_patch: Path, tmp_path: Path
) -> None:
    dest = tmp_path / "tree"
    build_case_tree(source.path, source.landing, defect_patch, dest)
    assert git(dest, "rev-parse", "HEAD") not in {source.landing, source.later}


def test_tree_working_copy_is_clean_after_commit(
    source: SourceRepo, defect_patch: Path, tmp_path: Path
) -> None:
    dest = tmp_path / "tree"
    build_case_tree(source.path, source.landing, defect_patch, dest)
    assert git(dest, "status", "--porcelain") == ""


def test_control_tree_matches_landed_tree_exactly(source: SourceRepo, tmp_path: Path) -> None:
    dest = tmp_path / "control"
    build_case_tree(source.path, source.landing, None, dest)
    assert (dest / "a.txt").read_text() == "one\ntwo\nthree\nfour\n"
    assert git(dest, "rev-parse", "HEAD^{tree}") == git(
        source.path, "rev-parse", f"{source.landing}^{{tree}}"
    )


def test_control_and_defect_trees_have_same_construction(
    source: SourceRepo, defect_patch: Path, tmp_path: Path
) -> None:
    control = tmp_path / "control"
    defect = tmp_path / "defect"
    build_case_tree(source.path, source.landing, None, control)
    build_case_tree(source.path, source.landing, defect_patch, defect)
    shape = ["rev-list", "--count", "HEAD"]
    assert git(control, *shape) == git(defect, *shape) == "2"
    assert git(control, "rev-parse", "HEAD~1") == git(defect, "rev-parse", "HEAD~1")
    assert git(control, "for-each-ref").count("\n") == git(defect, "for-each-ref").count("\n")


def test_tree_does_not_alter_source_repo(
    source: SourceRepo, defect_patch: Path, tmp_path: Path
) -> None:
    before = git(source.path, "for-each-ref")
    build_case_tree(source.path, source.landing, defect_patch, tmp_path / "tree")
    assert git(source.path, "for-each-ref") == before
    assert git(source.path, "status", "--porcelain") == ""


def test_tree_objects_are_not_hardlinked_to_source(
    source: SourceRepo, defect_patch: Path, tmp_path: Path
) -> None:
    dest = tmp_path / "tree"
    build_case_tree(source.path, source.landing, defect_patch, dest)
    source_objects = {
        p.stat().st_ino for p in (source.path / ".git" / "objects").rglob("*") if p.is_file()
    }
    dest_objects = {p.stat().st_ino for p in (dest / ".git" / "objects").rglob("*") if p.is_file()}
    assert dest_objects
    assert not source_objects & dest_objects


def test_patch_that_does_not_apply_raises_with_stderr(
    source: SourceRepo, bad_patch: Path, tmp_path: Path
) -> None:
    with pytest.raises(PatchDoesNotApply) as excinfo:
        build_case_tree(source.path, source.landing, bad_patch, tmp_path / "tree")
    assert "a.txt" in str(excinfo.value)
    assert "a.txt" in excinfo.value.stderr
