from __future__ import annotations

from pathlib import Path

from orchestra.tools import Git, ToolError


def _commit(git: Git, message: str) -> None:
    git.text("add", "-A")
    git.text("-c", "commit.gpgsign=false", "commit", "-m", message)


def test_real_repository_workflow(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git = Git(repo)
    git.text("init", "-b", "main")
    git.text("config", "user.name", "Test")
    git.text("config", "user.email", "test@example.com")
    blob = bytes(range(256))
    (repo / "shared.txt").write_text("base\n")
    (repo / "blob.bin").write_bytes(blob)
    _commit(git, "base")
    base = git.head()

    assert git.current_branch() == "main"
    assert git.status_porcelain() == ""
    assert git.show_bytes("HEAD", "blob.bin") == blob
    assert git.show_bytes("HEAD", "missing.bin") is None

    git.create_branch("side", "main")
    worktree = tmp_path / "side-worktree"
    git.add_worktree(worktree, "side")
    side = Git(worktree)
    assert side.current_branch() == "side"

    (worktree / "shared.txt").write_text("side change\n")
    _commit(side, "side change")
    (repo / "shared.txt").write_text("main change\n")
    _commit(git, "main change")

    assert git.is_ancestor(base, "main")
    assert git.is_ancestor(base, "side")
    assert not git.is_ancestor("main", "side")
    assert git.merge_base("main", "side") == base
    assert git.changed_paths(base, "side") == ("shared.txt",)

    result = git.merge("side")

    assert not result.clean
    assert result.unmerged == ("shared.txt",)
    assert "<<<<<<<" in (repo / "shared.txt").read_text()
    assert git.status_porcelain().startswith("UU shared.txt")

    git.text("merge", "--abort")
    assert git.head() == git.resolve("main")
    assert git.resolve("no-such-branch") is None

    try:
        git.is_ancestor("no-such-rev", "main")
    except ToolError as error:
        assert error.returncode is not None
    else:
        raise AssertionError("expected ToolError")
