from __future__ import annotations

import subprocess
from collections import deque
from pathlib import Path

import pytest

import orchestra.cli as cli
import orchestra.conductor.github_pr as github_pr
from orchestra.conductor.github_pr import (
    GitHubCheck,
    GitHubPRError,
    GitHubPRResult,
    GitHubREST,
    open_pull_request,
)
from orchestra.conductor.land import LandingCheck, LandingResult


class FakeGitHub:
    def __init__(self) -> None:
        self.events: list[str] = []
        self.body = ""
        self.check_batches: deque[tuple[GitHubCheck, ...]] = deque()
        self.status_batches: deque[tuple[str, ...]] = deque()

    def push_branch(self, remote: str, branch: str) -> None:
        self.events.append(f"push:{remote}:{branch}")

    def repository(self) -> str:
        self.events.append("repository")
        return "owner/repo"

    def create_pull_request(
        self, repository: str, head: str, base: str, title: str, body: str
    ) -> tuple[int, str]:
        self.events.append(f"create:{repository}:{head}:{base}:{title}")
        self.body = body
        return 42, "https://github.com/owner/repo/pull/42"

    def checks(self, repository: str, revision: str) -> tuple[GitHubCheck, ...]:
        self.events.append(f"checks:{repository}:{revision}")
        return self.check_batches.popleft()

    def statuses(self, repository: str, revision: str) -> tuple[str, ...]:
        self.events.append(f"statuses:{repository}:{revision}")
        return self.status_batches.popleft()


def _write_project(root: Path) -> str:
    root.mkdir()
    _git(root, "init", "-q", "-b", "phase/project-config")
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
    return _git(root, "rev-parse", "HEAD")


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _adapter(root: Path, client: FakeGitHub) -> GitHubPRResult:
    return open_pull_request(
        root,
        "## Look\nProof packet body\n",
        client=client,
        poll_interval_s=1,
        timeout_s=10,
        sleep=lambda _seconds: None,
        monotonic=lambda: 0,
    )


def test_github_pr_includes_proof_packet(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    github = FakeGitHub()
    github.check_batches.append((GitHubCheck("CI", "completed", "success"),))
    github.status_batches.append(("success",))

    result = _adapter(root, github)

    assert github.body == "## Look\nProof packet body\n"
    assert result.number == 42
    assert result.url.endswith("/pull/42")
    assert github.events[:3] == [
        "push:origin:phase/project-config",
        "repository",
        "create:owner/repo:phase/project-config:main:phase/project-config: phase proof",
    ]


def test_github_pr_waits_for_checks_to_complete(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    github = FakeGitHub()
    github.check_batches.extend(
        [
            (GitHubCheck("CI", "in_progress", None),),
            (GitHubCheck("CI", "completed", "success"),),
        ]
    )
    github.status_batches.extend([("pending",), ("success",)])
    sleeps: list[float] = []

    result = open_pull_request(
        root,
        "proof packet",
        client=github,
        poll_interval_s=2,
        timeout_s=10,
        sleep=sleeps.append,
        monotonic=lambda: 0,
    )

    assert result.result == "success"
    assert len([event for event in github.events if event.startswith("checks:")]) == 2
    assert sleeps == [2]


def test_github_pr_waits_for_checks_to_appear(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    github = FakeGitHub()
    github.check_batches.extend([(), (GitHubCheck("CI", "completed", "success"),)])
    github.status_batches.extend([(), ("success",)])
    sleeps: list[float] = []

    result = open_pull_request(
        root,
        "proof packet",
        client=github,
        poll_interval_s=2,
        timeout_s=10,
        sleep=sleeps.append,
        monotonic=lambda: 0,
    )

    assert result.result == "success"
    assert len([event for event in github.events if event.startswith("checks:")]) == 2
    assert sleeps == [2]


def test_github_pr_reports_final_ci_result(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    github = FakeGitHub()
    github.check_batches.append((GitHubCheck("CI", "completed", "failure"),))
    github.status_batches.append(("failure",))

    result = _adapter(root, github)

    assert result.result == "failure"
    assert result.checks[0].conclusion == "failure"
    assert result.statuses == ("failure",)


def test_github_pr_never_merges(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    github = FakeGitHub()
    github.check_batches.append((GitHubCheck("CI", "completed", "success"),))
    github.status_batches.append(("success",))

    _adapter(root, github)

    assert all("merge" not in event for event in github.events)
    assert not hasattr(github, "merge")


def test_github_rest_requires_token_without_gh_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)

    with pytest.raises(GitHubPRError, match="set GITHUB_TOKEN or GH_TOKEN"):
        GitHubREST(root)


def test_github_rest_uses_token_authenticated_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    monkeypatch.setenv("GH_TOKEN", "test-token")
    captured: list[object] = []

    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"number":7,"html_url":"https://github.com/owner/repo/pull/7"}'

    def fake_urlopen(request: object, timeout: float) -> Response:
        captured.extend((request, timeout))
        return Response()

    monkeypatch.setattr(github_pr, "urlopen", fake_urlopen)
    client = GitHubREST(root)
    number, url = client.create_pull_request("owner/repo", "topic", "main", "title", "proof")

    request = captured[0]
    assert number == 7
    assert url.endswith("/pull/7")
    assert request.full_url == "https://api.github.com/repos/owner/repo/pulls"
    assert request.get_header("Authorization") == "Bearer test-token"
    assert captured[1] == 30


def test_github_rest_derives_repository_from_git_remote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    _git(root, "remote", "add", "origin", "git@github.com:owner/repo.git")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    assert GitHubREST(root).repository() == "owner/repo"


def test_land_cli_reports_pull_request_and_final_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from orchestra.canon.types import Record

    packet: Record = {
        "id": "packet-id",
        "record_type": "conductor:proof-packet",
        "subject": "project-config",
        "payload": {"revision": "head-sha"},
        "lifecycle_state": "recorded",
        "relationships": {},
        "revision": "store-revision",
        "recorded_at": "now",
        "body": "proof packet",
    }

    class FakeProject:
        def list(self, record_type: str) -> list[Record]:
            assert record_type == "conductor:proof-packet"
            return [packet]

    def fake_open_pull_request(
        root: Path,
        proof_packet: str,
        *,
        base: str,
        remote: str,
        poll_interval_s: float,
        timeout_s: float,
    ) -> LandingResult:
        assert root == tmp_path.resolve()
        assert proof_packet == "proof packet"
        assert base == "main"
        assert remote == "origin"
        assert poll_interval_s == 10
        assert timeout_s == 1800
        return LandingResult(
            result="success",
            number=42,
            url="https://github.com/owner/repo/pull/42",
            head_sha="head-sha",
            checks=(LandingCheck("CI", "completed", "success"),),
            statuses=("success",),
        )

    monkeypatch.setattr(cli, "open_store", lambda _root: FakeProject())
    monkeypatch.setattr(cli, "git_head", lambda _root: "head-sha")
    monkeypatch.setattr(cli.land, "dispatch_land", fake_open_pull_request)

    exit_code = cli.main(["land", "--phase", "project-config", "--cwd", str(tmp_path)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert '"url": "https://github.com/owner/repo/pull/42"' in output
    assert '"result": "success"' in output
