"""GitHub pull-request landing adapter."""

from __future__ import annotations

import math
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from orchestra.canon.project_config import load_project_config
from orchestra.canon.types import JsonObject
from orchestra.tools import CliTool, Git, ToolError, ToolNotFoundError, Version, run_subprocess
from orchestra.tools.cli_tool import RunFn


@dataclass(frozen=True)
class GitHubCheck:
    name: str
    status: str
    conclusion: str | None


@dataclass(frozen=True)
class GitHubPRResult:
    number: int
    url: str
    head_sha: str
    checks: tuple[GitHubCheck, ...]
    statuses: tuple[str, ...]
    result: str


class GitHubPRError(RuntimeError):
    """GitHub pull-request creation or CI polling failed."""


class GitHubClient(Protocol):
    def push_branch(self, remote: str, branch: str) -> None: ...

    def find_pull_request(self, head: str) -> tuple[int, str] | None: ...

    def create_pull_request(
        self, head: str, base: str, title: str, body: str
    ) -> tuple[int, str]: ...

    def head_sha(self, number: int) -> str: ...

    def checks(self, number: int) -> tuple[GitHubCheck, ...]: ...


def open_pull_request(
    root: Path | str,
    proof_packet: str,
    *,
    base: str = "main",
    remote: str = "origin",
    title: str | None = None,
    poll_interval_s: float = 10,
    timeout_s: float = 1800,
    client: GitHubClient | None = None,
    sleep: Callable[[float], None] | None = None,
    monotonic: Callable[[], float] | None = None,
    adapter_config: JsonObject | None = None,
) -> GitHubPRResult:
    """Push a committed branch, open a PR with its proof packet, and await CI."""
    project_root = Path(root)
    config = load_project_config(project_root)
    adapter_config = adapter_config or config.land_config
    if config.merge_policy != "human":
        raise GitHubPRError("land.merge must remain human")
    if not proof_packet.strip():
        raise GitHubPRError("a phase proof packet is required to open a pull request")
    if not math.isfinite(poll_interval_s) or poll_interval_s <= 0:
        raise GitHubPRError("CI polling interval must be a positive finite number")
    if not math.isfinite(timeout_s) or timeout_s <= 0:
        raise GitHubPRError("CI timeout must be a positive finite number")

    git = Git(project_root)
    try:
        branch = git.current_branch()
        head_sha = git.head()
        dirty = git.status_porcelain()
    except ToolError as error:
        raise GitHubPRError(_git_error_message(error)) from error
    if dirty:
        raise GitHubPRError("the phase branch must be clean before opening a pull request")

    github = client or GitHubGh(project_root, remote, adapter_config)
    pr_title = title or f"{branch}: phase proof"
    sleep_fn = sleep if sleep is not None else time.sleep
    monotonic_fn = monotonic if monotonic is not None else time.monotonic
    try:
        github.push_branch(remote, branch)
        existing = github.find_pull_request(branch)
        if existing is None:
            number, url = github.create_pull_request(branch, base, pr_title, proof_packet)
        else:
            number, url = existing
        checks = wait_for_checks(
            github,
            number,
            head_sha=head_sha,
            poll_interval_s=poll_interval_s,
            timeout_s=timeout_s,
            sleep=sleep_fn,
            monotonic=monotonic_fn,
        )
    except ToolError as error:
        raise GitHubPRError(_tool_error_message(error)) from error
    return GitHubPRResult(
        number=number,
        url=url,
        head_sha=head_sha,
        checks=checks,
        statuses=(),
        result=_final_result(checks),
    )


def wait_for_checks(
    client: GitHubClient,
    number: int,
    *,
    head_sha: str,
    poll_interval_s: float,
    timeout_s: float,
    sleep: Callable[[float], None],
    monotonic: Callable[[], float],
) -> tuple[GitHubCheck, ...]:
    deadline = monotonic() + timeout_s
    while True:
        checks = client.checks(number)
        current = client.head_sha(number)
        if current != head_sha:
            raise GitHubPRError(
                f"pull request head changed from {head_sha} to {current} while waiting for checks"
            )
        if checks and all(check.status == "completed" for check in checks):
            return checks
        remaining = deadline - monotonic()
        if remaining <= 0:
            pending = [check.name for check in checks if check.status != "completed"]
            raise TimeoutError(
                "GitHub checks did not complete before timeout: " + ", ".join(pending)
            )
        sleep(min(poll_interval_s, remaining))


def _tool_error_message(error: ToolError) -> str:
    stderr = error.stderr.strip()
    return f"{error}: {stderr}" if stderr else str(error)


def _final_result(checks: Sequence[GitHubCheck]) -> str:
    failed = any(check.conclusion not in ("success", "neutral", "skipped") for check in checks)
    return "fail" if failed else "success"


def _git_error_message(error: ToolError) -> str:
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
        adapter_config: JsonObject | None = None,
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
            raise GitHubPRError("land.config.repository must use owner/repository format")
        self._repository: str | None = repository

    def push_branch(self, remote: str, branch: str) -> None:
        self._check_version()
        try:
            Git(self.root).push(remote, branch)
        except ToolError as error:
            raise GitHubPRError(_git_error_message(error)) from error

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
            raise GitHubPRError("gh pr list returned an unexpected shape")
        if not data:
            return None
        found = data[0]
        number = found.get("number") if isinstance(found, dict) else None
        url = found.get("url") if isinstance(found, dict) else None
        if isinstance(number, bool) or not isinstance(number, int) or not isinstance(url, str):
            raise GitHubPRError("gh pr list returned an unexpected shape")
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
            raise GitHubPRError("gh pr create printed no pull request URL")
        return self.pull_request(lines[-1])

    def pull_request(self, ref: str) -> tuple[int, str]:
        data = self._json("pr", "view", ref, "--json", "number,url", *self._repository_flags())
        if not isinstance(data, dict):
            raise GitHubPRError("gh pr view returned an unexpected shape")
        number = data.get("number")
        url = data.get("url")
        if isinstance(number, bool) or not isinstance(number, int) or not isinstance(url, str):
            raise GitHubPRError("gh pr view returned an unexpected shape")
        return number, url

    def head_sha(self, number: int) -> str:
        data = self._json(
            "pr", "view", str(number), "--json", "headRefOid", *self._repository_flags()
        )
        sha = data.get("headRefOid") if isinstance(data, dict) else None
        if not isinstance(sha, str) or not sha:
            raise GitHubPRError("gh pr view returned an unexpected shape")
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
            raise GitHubPRError("gh pr checks returned an unexpected shape")
        checks: list[GitHubCheck] = []
        for item in data:
            if not isinstance(item, dict):
                raise GitHubPRError("gh pr checks returned an unexpected shape")
            name = item.get("name")
            bucket = item.get("bucket")
            if not isinstance(name, str) or not isinstance(bucket, str):
                raise GitHubPRError("gh pr checks returned an unexpected shape")
            if bucket not in _BUCKET_STATES:
                raise GitHubPRError(f"gh pr checks returned unknown bucket: {bucket}")
            status, conclusion = _BUCKET_STATES[bucket]
            checks.append(GitHubCheck(name, status, conclusion))
        return tuple(checks)
