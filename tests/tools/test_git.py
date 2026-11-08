from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, overload

import pytest

from orchestra.tools import CliTool, Git, GitResult, MergeResult, ToolError, Version
from orchestra.tools.testing import scripted


class FakeGitRun:
    def __init__(
        self,
        returncode: int = 0,
        stdout: str | bytes = "",
        stderr: str = "",
        raises: BaseException | None = None,
        by_subcommand: Mapping[str, tuple[int, str]] | None = None,
    ) -> None:
        self.by_subcommand = by_subcommand or {}
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.raises = raises
        self.cwds: list[Path] = []
        self.argvs: list[list[str]] = []

    @overload
    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | None,
        timeout: float | None,
        capture_output: bool,
        text: Literal[True],
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str]: ...

    @overload
    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: bytes | None,
        timeout: float | None,
        capture_output: bool,
        text: Literal[False],
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[bytes]: ...

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | bytes | None,
        timeout: float | None,
        capture_output: bool,
        text: bool,
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
        if list(argv)[1:] == ["--version"]:
            if text:
                return subprocess.CompletedProcess(list(argv), 0, "git version 2.40.0\n", "")
            return subprocess.CompletedProcess(list(argv), 0, b"git version 2.40.0\n", b"")
        self.cwds.append(cwd)
        self.argvs.append(list(argv))
        if self.raises is not None:
            raise self.raises
        if argv[1] in self.by_subcommand:
            code, out = self.by_subcommand[argv[1]]
            return subprocess.CompletedProcess(list(argv), code, out, "")
        if text:
            out = self.stdout.decode() if isinstance(self.stdout, bytes) else self.stdout
            return subprocess.CompletedProcess(list(argv), self.returncode, out, self.stderr)
        raw = self.stdout.encode() if isinstance(self.stdout, str) else self.stdout
        return subprocess.CompletedProcess(list(argv), self.returncode, raw, self.stderr.encode())


def test_git_is_cli_tool_for_git() -> None:
    assert issubclass(Git, CliTool)
    assert Git.executable == "git"


def test_min_version_is_2_17() -> None:
    assert Git.min_version == Version(2, 17)


def test_runs_in_constructed_cwd(tmp_path: Path) -> None:
    fake = FakeGitRun(stdout="ok\n")
    Git(tmp_path, run=fake).run("status")
    assert fake.cwds == [tmp_path]


def test_run_returns_git_result(tmp_path: Path) -> None:
    fake = FakeGitRun(stdout="out", stderr="err")
    result = Git(tmp_path, run=fake).run("status")
    assert result == GitResult(0, "out", "err")
    assert fake.argvs == [["git", "status"]]


def test_run_does_not_raise_on_nonzero(tmp_path: Path) -> None:
    fake = FakeGitRun(returncode=128, stderr="fatal")
    result = Git(tmp_path, run=fake).run("status")
    assert result.returncode == 128
    assert result.stderr == "fatal"


def test_run_raises_tool_error_when_git_missing(tmp_path: Path) -> None:
    fake = FakeGitRun(raises=FileNotFoundError("git"))
    with pytest.raises(ToolError):
        Git(tmp_path, run=fake).run("status")


def test_run_raises_tool_error_on_timeout(tmp_path: Path) -> None:
    fake = FakeGitRun(raises=subprocess.TimeoutExpired(["git"], 1.0))
    with pytest.raises(ToolError) as info:
        Git(tmp_path, run=fake).run("status")
    assert "timed out" in str(info.value)


def test_text_returns_stripped_stdout(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "rev-parse", "HEAD"): "abc123\n"})
    assert Git(tmp_path, run=run).text("rev-parse", "HEAD") == "abc123"


def test_text_raises_on_nonzero(tmp_path: Path) -> None:
    fake = FakeGitRun(returncode=1, stderr="bad ref")
    with pytest.raises(ToolError) as info:
        Git(tmp_path, run=fake).text("rev-parse", "nope")
    assert info.value.returncode == 1
    assert info.value.stderr == "bad ref"


def test_show_bytes_returns_blob(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "show", "HEAD:a.bin"): b"\x00\xffdata"})
    assert Git(tmp_path, run=run).show_bytes("HEAD", "a.bin") == b"\x00\xffdata"


def test_show_bytes_missing_path_is_none(tmp_path: Path) -> None:
    fake = FakeGitRun(returncode=128, stderr="fatal: path missing")
    assert Git(tmp_path, run=fake).show_bytes("HEAD", "gone.txt") is None


def test_root(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "rev-parse", "--show-toplevel"): "/repo/top\n"})
    assert Git(tmp_path, run=run).root() == Path("/repo/top")


def test_head(tmp_path: Path) -> None:
    sha = "a" * 40
    run = scripted(Git, {("git", "rev-parse", "HEAD"): f"{sha}\n"})
    assert Git(tmp_path, run=run).head() == sha


def test_resolve_returns_sha(tmp_path: Path) -> None:
    sha = "b" * 40
    run = scripted(Git, {("git", "rev-parse", "--verify", "--quiet", "main^{commit}"): f"{sha}\n"})
    assert Git(tmp_path, run=run).resolve("main") == sha


def test_resolve_missing_is_none(tmp_path: Path) -> None:
    fake = FakeGitRun(returncode=1)
    assert Git(tmp_path, run=fake).resolve("nope") is None
    assert fake.argvs == [["git", "rev-parse", "--verify", "--quiet", "nope^{commit}"]]


def test_current_branch(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "symbolic-ref", "--short", "HEAD"): "feature/x\n"})
    assert Git(tmp_path, run=run).current_branch() == "feature/x"


def test_status_porcelain(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "status", "--porcelain"): " M a.py\n?? b.py\n"})
    assert Git(tmp_path, run=run).status_porcelain() == " M a.py\n?? b.py"


def test_is_ancestor(tmp_path: Path) -> None:
    assert Git(tmp_path, run=FakeGitRun(returncode=0)).is_ancestor("a", "b") is True
    assert Git(tmp_path, run=FakeGitRun(returncode=1)).is_ancestor("a", "b") is False
    with pytest.raises(ToolError) as info:
        Git(tmp_path, run=FakeGitRun(returncode=128, stderr="bad")).is_ancestor("a", "b")
    assert info.value.returncode == 128
    fake = FakeGitRun(returncode=0)
    Git(tmp_path, run=fake).is_ancestor("a", "b")
    assert fake.argvs == [["git", "merge-base", "--is-ancestor", "a", "b"]]


def test_merge_base(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "merge-base", "a", "b"): "c" * 40 + "\n"})
    assert Git(tmp_path, run=run).merge_base("a", "b") == "c" * 40


def test_changed_paths(tmp_path: Path) -> None:
    key = ("git", "diff", "--name-only", "--no-renames", "-z", "a..b")
    run = scripted(Git, {key: "x.py\0dir/y z.py\0"})
    assert Git(tmp_path, run=run).changed_paths("a", "b") == ("x.py", "dir/y z.py")
    empty = scripted(Git, {key: ""})
    assert Git(tmp_path, run=empty).changed_paths("a", "b") == ()


def test_merge_clean_and_conflicted(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "merge", "--no-edit", "topic"): "Merge made\n"})
    assert Git(tmp_path, run=run).merge("topic") == MergeResult(True, ())

    fake = FakeGitRun(by_subcommand={"merge": (1, ""), "ls-files": (0, "100644 abc 1\tf.py\n")})
    assert Git(tmp_path, run=fake).merge("topic").clean is False


def test_merge_result_lists_unmerged(tmp_path: Path) -> None:
    listing = "100644 a1 1\tf.py\n100644 a2 2\tf.py\n100644 a3 3\tf.py\n100644 b1 2\tg/h.py\n"

    fake = FakeGitRun(by_subcommand={"merge": (1, ""), "ls-files": (0, listing)})
    result = Git(tmp_path, run=fake).merge("topic")
    assert result == MergeResult(False, ("f.py", "g/h.py"))


def test_push_sets_upstream(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "push", "--set-upstream", "origin", "feat"): ""})
    Git(tmp_path, run=run).push("origin", "feat")
    assert run.calls[-1] == ("git", "push", "--set-upstream", "origin", "feat")


def test_create_branch(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "branch", "feat", "main"): ""})
    Git(tmp_path, run=run).create_branch("feat", "main")
    assert run.calls[-1] == ("git", "branch", "feat", "main")


def test_add_worktree(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "worktree", "add", "/wt/feat", "feat"): ""})
    Git(tmp_path, run=run).add_worktree(Path("/wt/feat"), "feat")
    assert run.calls[-1] == ("git", "worktree", "add", "/wt/feat", "feat")


def test_git_has_no_default_timeout(tmp_path: Path) -> None:
    seen: list[float | None] = []

    def run(argv: Sequence[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        timeout = kwargs["timeout"]
        assert timeout is None or isinstance(timeout, float)
        seen.append(timeout)
        return subprocess.CompletedProcess(list(argv), 0, "git version 2.40.0\n", "")

    Git(tmp_path, run=run).run("status")  # pyright: ignore[reportArgumentType]
    assert seen == [None, None]


def test_merge_result_carries_output(tmp_path: Path) -> None:
    fake = FakeGitRun(by_subcommand={"merge": (1, "merge out"), "ls-files": (0, "")})
    result = Git(tmp_path, run=fake).merge("topic")
    assert result == MergeResult(False, (), "merge out")


def test_remove_worktree_never_forces(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "worktree", "remove", "/wt/feat"): ""})
    Git(tmp_path, run=run).remove_worktree(Path("/wt/feat"))
    assert run.calls[-1] == ("git", "worktree", "remove", "/wt/feat")


def test_remove_worktree_failure_raises(tmp_path: Path) -> None:
    run = FakeGitRun(by_subcommand={"worktree": (128, "contains modified or untracked files")})
    with pytest.raises(ToolError):
        Git(tmp_path, run=run).remove_worktree(Path("/wt/feat"))


def test_delete_branch_forces_the_delete(tmp_path: Path) -> None:
    run = scripted(Git, {("git", "branch", "-D", "feat"): ""})
    Git(tmp_path, run=run).delete_branch("feat")
    assert run.calls[-1] == ("git", "branch", "-D", "feat")


def test_branch_tip_resolves_the_local_branch(tmp_path: Path) -> None:
    tip = "a" * 40
    argv = ("git", "rev-parse", "--verify", "--quiet", "refs/heads/feat^{commit}")
    run = scripted(Git, {argv: f"{tip}\n"})
    assert Git(tmp_path, run=run).branch_tip("feat") == tip


def test_branch_tip_is_none_for_a_missing_branch(tmp_path: Path) -> None:
    run = FakeGitRun(by_subcommand={"rev-parse": (1, "")})
    assert Git(tmp_path, run=run).branch_tip("gone") is None
