"""GitHub pull-request landing adapter."""

from __future__ import annotations

import json
import math
import os
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from orchestra.canon.git_backend import run_git
from orchestra.canon.project_config import load_project_config
from orchestra.canon.types import JsonObject, JsonValue
from orchestra.tools import CliTool, Version, run_subprocess
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

    def repository(self) -> str: ...

    def create_pull_request(
        self, repository: str, head: str, base: str, title: str, body: str
    ) -> tuple[int, str]: ...

    def checks(self, repository: str, revision: str) -> tuple[GitHubCheck, ...]: ...

    def statuses(self, repository: str, revision: str) -> tuple[str, ...]: ...


class GitHubREST:
    def __init__(
        self,
        root: Path,
        remote: str = "origin",
        adapter_config: JsonObject | None = None,
    ) -> None:
        self.root = root
        self.adapter_config = adapter_config or {}
        configured_remote = self.adapter_config.get("remote", remote)
        if not isinstance(configured_remote, str) or not configured_remote:
            raise GitHubPRError("land.config.remote must be a non-empty string")
        self.remote = configured_remote
        token_env = self.adapter_config.get("token_env", "GITHUB_TOKEN")
        if not isinstance(token_env, str) or not token_env:
            raise GitHubPRError("land.config.token_env must be a non-empty string")
        self.token = os.environ.get(token_env) or os.environ.get("GH_TOKEN")
        if not self.token:
            raise GitHubPRError(f"set {token_env} or GH_TOKEN to use the GitHub API")

    def push_branch(self, remote: str, branch: str) -> None:
        _git(self.root, "push", "--set-upstream", remote, branch)

    def repository(self) -> str:
        configured_repository = self.adapter_config.get("repository")
        if configured_repository is not None:
            if (
                not isinstance(configured_repository, str)
                or len(configured_repository.split("/")) != 2
            ):
                raise GitHubPRError("land.config.repository must use owner/repository format")
            return configured_repository
        remote_url = _git(self.root, "remote", "get-url", self.remote)
        parsed = urlparse(remote_url)
        if parsed.hostname == "github.com":
            repository = parsed.path.lstrip("/")
        elif parsed.scheme == "" and remote_url.startswith("git@github.com:"):
            repository = remote_url.removeprefix("git@github.com:")
        else:
            raise GitHubPRError(f"unsupported GitHub remote URL: {remote_url}")
        repository = repository.removesuffix(".git").strip("/")
        if len(repository.split("/")) != 2:
            raise GitHubPRError(f"cannot determine owner/repository from remote: {remote_url}")
        return repository

    def create_pull_request(
        self, repository: str, head: str, base: str, title: str, body: str
    ) -> tuple[int, str]:
        response = self._request(
            "POST",
            f"repos/{repository}/pulls",
            {"title": title, "head": head, "base": base, "body": body},
        )
        number = response.get("number")
        url = response.get("html_url")
        if not isinstance(number, int) or not isinstance(url, str):
            raise GitHubPRError("GitHub returned a pull request without number and URL")
        return number, url

    def checks(self, repository: str, revision: str) -> tuple[GitHubCheck, ...]:
        result: list[GitHubCheck] = []
        for page in self._pages(f"repos/{repository}/commits/{revision}/check-runs"):
            checks = page.get("check_runs")
            if not isinstance(checks, list):
                raise GitHubPRError("GitHub returned malformed check runs")
            for check in checks:
                if not isinstance(check, dict):
                    raise GitHubPRError("GitHub returned a malformed check run")
                name, status, conclusion = (
                    check.get("name"),
                    check.get("status"),
                    check.get("conclusion"),
                )
                if not isinstance(name, str) or not isinstance(status, str):
                    raise GitHubPRError("GitHub returned a malformed check run")
                result.append(
                    GitHubCheck(name, status, conclusion if isinstance(conclusion, str) else None)
                )
        return tuple(result)

    def statuses(self, repository: str, revision: str) -> tuple[str, ...]:
        response = self._request("GET", f"repos/{repository}/commits/{revision}/status")
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

    def _pages(self, path: str) -> tuple[JsonObject, ...]:
        pages: list[JsonObject] = []
        page = 1
        while True:
            response = self._request("GET", f"{path}?per_page=100&page={page}")
            pages.append(response)
            check_runs = response.get("check_runs")
            if not isinstance(check_runs, list):
                raise GitHubPRError("GitHub returned malformed check runs")
            if len(check_runs) < 100:
                return tuple(pages)
            page += 1

    def _request(self, method: str, path: str, body: dict[str, str] | None = None) -> JsonObject:
        encoded_path = quote(path, safe="/?=&")
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(
            f"https://api.github.com/{encoded_path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                **({"Content-Type": "application/json"} if data is not None else {}),
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                payload: JsonValue = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GitHubPRError(f"GitHub API returned HTTP {exc.code}: {detail}") from exc
        except (URLError, OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise GitHubPRError(f"GitHub API request failed: {exc}") from exc
        if not isinstance(payload, dict):
            raise GitHubPRError("GitHub returned a non-object API response")
        return payload


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

    branch = _git(project_root, "symbolic-ref", "--short", "HEAD")
    head_sha = _git(project_root, "rev-parse", "HEAD")
    if _git(project_root, "status", "--porcelain"):
        raise GitHubPRError("the phase branch must be clean before opening a pull request")

    github = client or GitHubREST(project_root, remote, adapter_config)
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
    return "fail" if failed_checks or failed_statuses else "success"


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


_REPOSITORY = re.compile(r"[^/\s]+/[^/\s]+")


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

    def _repository_flags(self) -> list[str]:
        return ["-R", self._repository] if self._repository else []

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
