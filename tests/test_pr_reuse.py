from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from orchestra.conductor.github_pr import (
    GitHubCheck,
    GitHubGh,
    GitHubPRError,
    GitHubPRResult,
    open_pull_request,
)
from orchestra.tools import Version
from orchestra.tools.testing import ScriptedRun

PR_URL = "https://github.com/owner/repo/pull/42"


class RecordingGitHub:
    def __init__(
        self, head: str, existing: tuple[int, str] | None, *, lookup_fails: bool = False
    ) -> None:
        self.events: list[str] = []
        self.head = head
        self.existing = existing
        self.lookup_fails = lookup_fails

    def push_branch(self, remote: str, branch: str) -> None:
        self.events.append(f"push:{remote}:{branch}")

    def find_pull_request(self, head: str) -> tuple[int, str] | None:
        self.events.append(f"find:{head}")
        if self.lookup_fails:
            raise GitHubPRError("gh pr list failed")
        return self.existing

    def create_pull_request(self, head: str, base: str, title: str, body: str) -> tuple[int, str]:
        self.events.append(f"create:{head}:{base}")
        if self.existing is not None:
            raise GitHubPRError("a pull request for this branch already exists")
        return 42, PR_URL

    def head_sha(self, number: int) -> str:
        return self.head

    def checks(self, number: int) -> tuple[GitHubCheck, ...]:
        return (GitHubCheck("CI", "completed", "success"),)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "phase/land-to-close")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "test")
    (root / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["unit"]\n\n'
        '[verify.unit]\nrunner = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]\n\n'
        '[land]\nadapter = "github-pr"\nmerge = "human"\n',
        encoding="utf-8",
    )
    _git(root, "add", "orchestra.toml")
    _git(root, "commit", "-qm", "phase")
    return root


def _land(root: Path, client: RecordingGitHub) -> GitHubPRResult:
    return open_pull_request(
        root,
        "## Look\nproof packet\n",
        client=client,
        poll_interval_s=1,
        timeout_s=10,
        sleep=lambda _seconds: None,
        monotonic=lambda: 0,
    )


def test_rerun_pushes_new_commits(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    github = RecordingGitHub(_git(root, "rev-parse", "HEAD"), existing=(42, PR_URL))

    result = _land(root, github)

    assert "push:origin:phase/land-to-close" in github.events
    assert (result.number, result.url) == (42, PR_URL)
    assert result.result == "success"


def test_rerun_opens_no_second_pull_request(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    github = RecordingGitHub(_git(root, "rev-parse", "HEAD"), existing=(42, PR_URL))

    _land(root, github)

    assert not [event for event in github.events if event.startswith("create:")]


def test_first_land_creates_the_pull_request(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    github = RecordingGitHub(_git(root, "rev-parse", "HEAD"), existing=None)

    result = _land(root, github)

    assert [event for event in github.events if event.startswith("create:")] == [
        "create:phase/land-to-close:main"
    ]
    assert result.number == 42


def test_land_stops_when_the_lookup_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    github = RecordingGitHub(_git(root, "rev-parse", "HEAD"), existing=None, lookup_fails=True)

    with pytest.raises(GitHubPRError):
        _land(root, github)

    assert not [event for event in github.events if event.startswith("create:")]


def test_gh_lookup_returns_the_open_pull_request_for_the_branch(tmp_path: Path) -> None:
    argv = (
        "gh", "pr", "list", "--head", "phase/land-to-close", "--state", "open",
        "--json", "number,url",
    )  # fmt: skip
    run = ScriptedRun(GitHubGh, {argv: json.dumps([{"number": 42, "url": PR_URL}])}, Version(2, 50))

    found = GitHubGh(tmp_path, run=run).find_pull_request("phase/land-to-close")

    assert found == (42, PR_URL)
    assert argv in run.calls


def test_gh_lookup_returns_none_when_no_pull_request_is_open(tmp_path: Path) -> None:
    argv = (
        "gh", "pr", "list", "--head", "phase/land-to-close", "--state", "open",
        "--json", "number,url",
    )  # fmt: skip
    run = ScriptedRun(GitHubGh, {argv: "[]"}, Version(2, 50))

    assert GitHubGh(tmp_path, run=run).find_pull_request("phase/land-to-close") is None
