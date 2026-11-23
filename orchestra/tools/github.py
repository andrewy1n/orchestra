from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from orchestra.tools.cli_tool import CliTool, RunFn, run_subprocess
from orchestra.tools.errors import ToolError, ToolNotFoundError
from orchestra.tools.git import Git
from orchestra.tools.version import Version


class GitHubError(ToolError):
    def __init__(
        self,
        message: str,
        argv: Sequence[str] = (),
        returncode: int | None = None,
        stderr: str = "",
    ) -> None:
        super().__init__(message, argv, returncode, stderr)


@dataclass(frozen=True)
class GitHubCheck:
    name: str
    status: str
    conclusion: str | None


def git_error_message(error: ToolError) -> str:
    if isinstance(error, ToolNotFoundError):
        return "git executable not found"
    return error.stderr.strip() or str(error)


_REPOSITORY = re.compile(r"[^/\s]+/[^/\s]+")

_BUCKET_STATES: dict[str, tuple[str, str | None]] = {
    "pass": ("completed", "success"),
    "fail": ("completed", "failure"),
    "pending": ("in_progress", None),
    "skipping": ("completed", "skipped"),
    "cancel": ("completed", "cancelled"),
}


class GitHubGh(CliTool):
    executable = "gh"
    min_version = Version(2, 50)

    def __init__(
        self,
        root: Path,
        remote: str = "origin",
        adapter_config: Mapping[str, object] | None = None,
        *,
        run: RunFn = run_subprocess,
    ) -> None:
        super().__init__(root, run=run)
        self.root = root
        self.remote = remote
        repository = (adapter_config or {}).get("repository")
        if repository is not None and (
            not isinstance(repository, str) or not _REPOSITORY.fullmatch(repository)
        ):
            raise GitHubError("repository must use owner/repository format")
        self._repository: str | None = repository

    def push_branch(self, remote: str, branch: str) -> None:
        self._check_version()
        try:
            Git(self.root).push(remote, branch)
        except ToolError as error:
            raise GitHubError(git_error_message(error), error.argv, error.returncode, "") from error

    def _repository_flags(self) -> list[str]:
        return ["-R", self._repository] if self._repository else []

    def find_pull_request(self, head: str) -> tuple[int, str] | None:
        data = self._json(
            "pr",
            "list",
            "--head",
            head,
            "--state",
            "open",
            "--json",
            "number,url",
            *self._repository_flags(),
        )
        if not isinstance(data, list):
            raise GitHubError("gh pr list returned an unexpected shape")
        if not data:
            return None
        found = data[0]
        number = found.get("number") if isinstance(found, dict) else None
        url = found.get("url") if isinstance(found, dict) else None
        if isinstance(number, bool) or not isinstance(number, int) or not isinstance(url, str):
            raise GitHubError("gh pr list returned an unexpected shape")
        return number, url

    def create_pull_request(self, head: str, base: str, title: str, body: str) -> tuple[int, str]:
        output = self._text(
            "pr",
            "create",
            "--base",
            base,
            "--head",
            head,
            "--title",
            title,
            "--body-file",
            "-",
            *self._repository_flags(),
            input=body,
        )
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if not lines:
            raise GitHubError("gh pr create printed no pull request URL")
        return self.pull_request(lines[-1])

    def update_pull_request(self, number: int, title: str, body: str) -> None:
        self._text(
            "pr",
            "edit",
            str(number),
            "--title",
            title,
            "--body-file",
            "-",
            *self._repository_flags(),
            input=body,
        )

    def pull_request(self, ref: str) -> tuple[int, str]:
        data = self._json("pr", "view", ref, "--json", "number,url", *self._repository_flags())
        if not isinstance(data, dict):
            raise GitHubError("gh pr view returned an unexpected shape")
        number = data.get("number")
        url = data.get("url")
        if isinstance(number, bool) or not isinstance(number, int) or not isinstance(url, str):
            raise GitHubError("gh pr view returned an unexpected shape")
        return number, url

    def pull_request_state(self, number: int) -> tuple[str, str]:
        data = self._json(
            "pr", "view", str(number), "--json", "state,headRefOid", *self._repository_flags()
        )
        state = data.get("state") if isinstance(data, dict) else None
        sha = data.get("headRefOid") if isinstance(data, dict) else None
        if not isinstance(state, str) or not state or not isinstance(sha, str) or not sha:
            raise GitHubError("gh pr view returned an unexpected shape")
        return state, sha

    def head_sha(self, number: int) -> str:
        data = self._json(
            "pr", "view", str(number), "--json", "headRefOid", *self._repository_flags()
        )
        sha = data.get("headRefOid") if isinstance(data, dict) else None
        if not isinstance(sha, str) or not sha:
            raise GitHubError("gh pr view returned an unexpected shape")
        return sha

    def checks(self, number: int) -> tuple[GitHubCheck, ...]:
        try:
            data = self._json(
                "pr",
                "checks",
                str(number),
                "--json",
                "name,state,bucket",
                *self._repository_flags(),
            )
        except ToolError as error:
            if "no checks reported" in error.stderr:
                return ()
            raise
        if not isinstance(data, list):
            raise GitHubError("gh pr checks returned an unexpected shape")
        checks: list[GitHubCheck] = []
        for item in data:
            if not isinstance(item, dict):
                raise GitHubError("gh pr checks returned an unexpected shape")
            name = item.get("name")
            bucket = item.get("bucket")
            if not isinstance(name, str) or not isinstance(bucket, str):
                raise GitHubError("gh pr checks returned an unexpected shape")
            if bucket not in _BUCKET_STATES:
                raise GitHubError(f"gh pr checks returned unknown bucket: {bucket}")
            status, conclusion = _BUCKET_STATES[bucket]
            checks.append(GitHubCheck(name, status, conclusion))
        return tuple(checks)
