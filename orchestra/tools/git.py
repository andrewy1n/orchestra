from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from orchestra.tools.cli_tool import CliTool
from orchestra.tools.errors import ToolError
from orchestra.tools.version import Version


@dataclass(frozen=True)
class GitResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class MergeResult:
    clean: bool
    unmerged: tuple[str, ...]


class Git(CliTool):
    executable: ClassVar[str] = "git"
    min_version: ClassVar[Version] = Version(2, 17)

    def run(self, *args: str, input: str | None = None) -> GitResult:
        self._check_version()
        argv = [self.executable, *args]
        try:
            result = self._run(
                argv,
                cwd=self._cwd,
                input=input,
                timeout=self._timeout,
                capture_output=True,
                text=True,
                check=False,
                env=self._env,
            )
        except OSError as error:
            raise ToolError(f"cannot run {argv[0]}: {error}", argv, None, "") from error
        except subprocess.TimeoutExpired as error:
            raise ToolError(
                f"{argv[0]} timed out after {self._timeout}s", argv, None, ""
            ) from error
        return GitResult(result.returncode, result.stdout, result.stderr)

    def _checked(self, *args: str, input: str | None = None) -> GitResult:
        result = self.run(*args, input=input)
        if result.returncode != 0:
            raise ToolError(
                f"{self.executable} exited with code {result.returncode}",
                [self.executable, *args],
                result.returncode,
                result.stderr,
            )
        return result

    def text(self, *args: str, input: str | None = None) -> str:
        return self._checked(*args, input=input).stdout.strip()

    def root(self) -> Path:
        return Path(self.text("rev-parse", "--show-toplevel"))

    def head(self) -> str:
        return self.text("rev-parse", "HEAD")

    def resolve(self, rev: str) -> str | None:
        result = self.run("rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def current_branch(self) -> str:
        return self.text("symbolic-ref", "--short", "HEAD")

    def status_porcelain(self) -> str:
        return self._checked("status", "--porcelain").stdout.removesuffix("\n")

    def is_ancestor(self, a: str, b: str) -> bool:
        result = self.run("merge-base", "--is-ancestor", a, b)
        if result.returncode == 0:
            return True
        if result.returncode == 1:
            return False
        raise ToolError(
            f"{self.executable} exited with code {result.returncode}",
            [self.executable, "merge-base", "--is-ancestor", a, b],
            result.returncode,
            result.stderr,
        )

    def merge_base(self, a: str, b: str) -> str:
        return self.text("merge-base", a, b)

    def changed_paths(self, a: str, b: str) -> tuple[str, ...]:
        out = self._checked("diff", "--name-only", "--no-renames", "-z", f"{a}..{b}").stdout
        return tuple(path for path in out.split("\0") if path)

    def merge(self, ref: str) -> MergeResult:
        if self.run("merge", "--no-edit", ref).returncode == 0:
            return MergeResult(True, ())
        listing = self.text("ls-files", "--unmerged")
        paths = (line.split("\t", 1)[1] for line in listing.splitlines() if "\t" in line)
        return MergeResult(False, tuple(dict.fromkeys(paths)))

    def push(self, remote: str, branch: str) -> None:
        self._checked("push", "--set-upstream", remote, branch)

    def create_branch(self, name: str, start: str) -> None:
        self._checked("branch", name, start)

    def add_worktree(self, path: Path | str, branch: str) -> None:
        self._checked("worktree", "add", str(path), branch)

    def show_bytes(self, revision: str, path: str) -> bytes | None:
        self._check_version()
        argv: Sequence[str] = [self.executable, "show", f"{revision}:{path}"]
        try:
            result = self._run(
                argv,
                cwd=self._cwd,
                input=None,
                timeout=self._timeout,
                capture_output=True,
                text=False,
                check=False,
                env=self._env,
            )
        except OSError as error:
            raise ToolError(f"cannot run {argv[0]}: {error}", argv, None, "") from error
        except subprocess.TimeoutExpired as error:
            raise ToolError(
                f"{argv[0]} timed out after {self._timeout}s", argv, None, ""
            ) from error
        if result.returncode != 0:
            return None
        return result.stdout
