"""GitHub pull-request landing adapter."""

from __future__ import annotations

import json
import math
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from orchestra.canon.git_backend import run_git
from orchestra.canon.project_config import load_project_config
from orchestra.canon.types import JsonValue


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

    def repository(self) -> str: ...

    def create_pull_request(
        self, repository: str, head: str, base: str, title: str, body: str
    ) -> tuple[int, str]: ...

    def checks(self, repository: str, revision: str) -> tuple[GitHubCheck, ...]: ...

    def statuses(self, repository: str, revision: str) -> tuple[str, ...]: ...


class GitHubCLI:
    def __init__(self, root: Path) -> None:
        self.root = root

    def push_branch(self, remote: str, branch: str) -> None:
        _git(self.root, "push", "--set-upstream", remote, branch)

    def repository(self) -> str:
        return self._run(
            "gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"
        ).strip()

    def create_pull_request(
        self, repository: str, head: str, base: str, title: str, body: str
    ) -> tuple[int, str]:
        response = _json_object(
            self._run(
                "gh",
                "api",
                f"repos/{repository}/pulls",
                "--method",
                "POST",
                "--input",
                "-",
                input_text=json.dumps({"title": title, "head": head, "base": base, "body": body}),
            )
        )
        number = response.get("number")
        url = response.get("html_url")
        if not isinstance(number, int) or not isinstance(url, str):
            raise GitHubPRError("GitHub returned a pull request without number and URL")
        return number, url

    def checks(self, repository: str, revision: str) -> tuple[GitHubCheck, ...]:
        output = self._run(
            "gh",
            "api",
            f"repos/{repository}/commits/{revision}/check-runs",
            "--paginate",
            "--jq",
            ".check_runs[] | {name: .name, status: .status, conclusion: .conclusion}",
        )
        result: list[GitHubCheck] = []
        for line in output.splitlines():
            if not line.strip():
                continue
            check = _json_object(line)
            name = check.get("name")
            status = check.get("status")
            conclusion = check.get("conclusion")
            if not isinstance(name, str) or not isinstance(status, str):
                raise GitHubPRError("GitHub returned a malformed check run")
            result.append(
                GitHubCheck(
                    name=name,
                    status=status,
                    conclusion=conclusion if isinstance(conclusion, str) else None,
                )
            )
        return tuple(result)

    def statuses(self, repository: str, revision: str) -> tuple[str, ...]:
        response = _json_object(
            self._run("gh", "api", f"repos/{repository}/commits/{revision}/status")
        )
        values = response.get("statuses")
        if not isinstance(values, list):
            raise GitHubPRError("GitHub returned malformed commit statuses")
        statuses: list[str] = []
        for value in values:
            if not isinstance(value, dict):
                raise GitHubPRError("GitHub returned a malformed commit status")
            state = value.get("state")
            if not isinstance(state, str):
                raise GitHubPRError("GitHub returned a commit status without state")
            statuses.append(state)
        return tuple(statuses)

    def _run(self, *argv: str, input_text: str | None = None) -> str:
        try:
            completed = subprocess.run(
                list(argv),
                cwd=self.root,
                input=input_text,
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise GitHubPRError(f"required executable not found: {argv[0]}") from exc
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip()
            raise GitHubPRError(detail or f"command failed: {argv[0]}")
        return completed.stdout


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
) -> GitHubPRResult:
    """Push a committed branch, open a PR with its proof packet, and await CI."""
    project_root = Path(root)
    config = load_project_config(project_root)
    if config.land_adapter != "github-pr":
        raise GitHubPRError("orchestra.toml must select land.adapter = github-pr")
    if config.merge_policy != "human":
        raise GitHubPRError("land.merge must remain human")
    if not proof_packet.strip():
        raise GitHubPRError("a phase proof packet is required to open a pull request")
    if not math.isfinite(poll_interval_s) or poll_interval_s <= 0:
        raise GitHubPRError("CI polling interval must be a positive finite number")
    if not math.isfinite(timeout_s) or timeout_s <= 0:
        raise GitHubPRError("CI timeout must be a positive finite number")

    branch = _git(project_root, "symbolic-ref", "--short", "HEAD")
    head_sha = _git(project_root, "rev-parse", "HEAD")
    if _git(project_root, "status", "--porcelain"):
        raise GitHubPRError("the phase branch must be clean before opening a pull request")

    github = client or GitHubCLI(project_root)
    github.push_branch(remote, branch)
    repository = github.repository()
    pr_title = title or f"{branch}: phase proof"
    number, url = github.create_pull_request(repository, branch, base, pr_title, proof_packet)
    sleep_fn = sleep if sleep is not None else time.sleep
    monotonic_fn = monotonic if monotonic is not None else time.monotonic
    checks, statuses = wait_for_checks(
        github,
        repository,
        head_sha,
        poll_interval_s=poll_interval_s,
        timeout_s=timeout_s,
        sleep=sleep_fn,
        monotonic=monotonic_fn,
    )
    return GitHubPRResult(
        number=number,
        url=url,
        head_sha=head_sha,
        checks=checks,
        statuses=statuses,
        result=_final_result(checks, statuses),
    )


def wait_for_checks(
    client: GitHubClient,
    repository: str,
    revision: str,
    *,
    poll_interval_s: float,
    timeout_s: float,
    sleep: Callable[[float], None],
    monotonic: Callable[[], float],
) -> tuple[tuple[GitHubCheck, ...], tuple[str, ...]]:
    deadline = monotonic() + timeout_s
    while True:
        checks = client.checks(repository, revision)
        statuses = client.statuses(repository, revision)
        if (
            (checks or statuses)
            and all(check.status == "completed" for check in checks)
            and all(status != "pending" for status in statuses)
        ):
            return checks, statuses
        remaining = deadline - monotonic()
        if remaining <= 0:
            pending = [check.name for check in checks if check.status != "completed"]
            pending.extend(f"commit status: {status}" for status in statuses if status == "pending")
            raise TimeoutError(
                "GitHub checks did not complete before timeout: " + ", ".join(pending)
            )
        sleep(min(poll_interval_s, remaining))


def _final_result(checks: Sequence[GitHubCheck], statuses: Sequence[str]) -> str:
    failed_checks = any(
        check.conclusion not in ("success", "neutral", "skipped") for check in checks
    )
    failed_statuses = any(status != "success" for status in statuses)
    return "failure" if failed_checks or failed_statuses else "success"


def _git(root: Path, *args: str) -> str:
    try:
        completed = run_git(
            root,
            *args,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise GitHubPRError("git executable not found") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise GitHubPRError(detail or f"git command failed: {' '.join(args)}")
    return completed.stdout.strip()


def _json_object(text: str) -> dict[str, JsonValue]:
    try:
        value: JsonValue = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GitHubPRError("GitHub returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise GitHubPRError("GitHub returned a non-object response")
    return value
