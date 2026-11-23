"""GitHub pull-request landing adapter."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from orchestra.canon.project_config import load_project_config
from orchestra.conductor.landing.landing import pull_request_body
from orchestra.tools import Git, ToolError, ToolNotFoundError
from orchestra.tools.github import GitHubCheck, GitHubError, GitHubGh


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

    def update_pull_request(self, number: int, title: str, body: str) -> None: ...

    def head_sha(self, number: int) -> str: ...

    def checks(self, number: int) -> tuple[GitHubCheck, ...]: ...


def open_pull_request(
    root: Path | str,
    proof_packet: str,
    *,
    base: str = "main",
    remote: str = "origin",
    title: str | None = None,
    description: Mapping[str, str] | None = None,
    poll_interval_s: float = 10,
    timeout_s: float = 1800,
    client: GitHubClient,
    sleep: Callable[[float], None] | None = None,
    monotonic: Callable[[], float] | None = None,
) -> GitHubPRResult:
    """Publish a committed branch and wait for CI if merge_evidence is unset."""
    project_root = Path(root)
    config = load_project_config(project_root)
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

    pr_title = title or f"{branch}: phase proof"
    sleep_fn = sleep if sleep is not None else time.sleep
    monotonic_fn = monotonic if monotonic is not None else time.monotonic
    try:
        client.push_branch(remote, branch)
        existing = client.find_pull_request(branch)
        body = pull_request_body(description or {}, proof_packet)
        if existing is None:
            number, url = client.create_pull_request(branch, base, pr_title, body)
        else:
            number, url = existing
            if description:
                client.update_pull_request(number, pr_title, body)
        if config.merge_evidence_adapter is not None:
            current = client.head_sha(number)
            if current != head_sha:
                raise GitHubPRError(
                    f"published pull request head is {current}, expected {head_sha}"
                )
            checks: tuple[GitHubCheck, ...] = ()
        else:
            checks = wait_for_checks(
                client,
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


def github_client(root: Path, remote: str = "origin") -> GitHubGh:
    try:
        return GitHubGh(root, remote, load_project_config(root).land_config)
    except GitHubError as error:
        raise GitHubPRError(str(error)) from error


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
