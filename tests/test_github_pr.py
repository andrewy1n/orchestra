from __future__ import annotations

import json
import subprocess
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Literal, overload

import pytest

import orchestra.cli as cli
import orchestra.conductor.github_pr as github_pr
from orchestra.canon.types import JsonObject
from orchestra.conductor.github_pr import (
    GitHubCheck,
    GitHubClient,
    GitHubGh,
    GitHubPRError,
    GitHubPRResult,
    open_pull_request,
    wait_for_checks,
)
from orchestra.conductor.land import LandingCheck, LandingResult, dispatch_land


class FakeGitHub:
    def __init__(self) -> None:
        self.events: list[str] = []
        self.body = ""
        self.check_batches: deque[tuple[GitHubCheck, ...]] = deque()

    def push_branch(self, remote: str, branch: str) -> None:
        self.events.append(f"push:{remote}:{branch}")

    def create_pull_request(self, head: str, base: str, title: str, body: str) -> tuple[int, str]:
        self.events.append(f"create:{head}:{base}:{title}")
        self.body = body
        return 42, "https://github.com/owner/repo/pull/42"

    def checks(self, number: int) -> tuple[GitHubCheck, ...]:
        self.events.append(f"checks:{number}")
        return self.check_batches.popleft()


class ScriptedGh:
    def __init__(
        self,
        version: str = "gh version 2.50.0 (2024-06-01)\n",
        failures: dict[tuple[str, ...], tuple[int, str]] | None = None,
        responses: dict[tuple[str, ...], str] | None = None,
        missing: bool = False,
    ) -> None:
        self.version = version
        self.failures = failures or {}
        self.responses = responses or {}
        self.missing = missing
        self.calls: list[tuple[str, ...]] = []

    @overload
    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | None,
        timeout: float,
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
        timeout: float,
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
        timeout: float,
        capture_output: bool,
        text: bool,
        check: bool,
        env: Mapping[str, str] | None,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
        key = tuple(argv)
        self.calls.append(key)
        if self.missing:
            raise FileNotFoundError(2, "No such file or directory", "gh")
        if key[1:] == ("--version",):
            return subprocess.CompletedProcess(list(key), 0, self.version, "")
        for prefix, (code, stderr) in self.failures.items():
            if key[: len(prefix)] == prefix:
                return subprocess.CompletedProcess(list(key), code, "", stderr)
        for prefix, stdout in self.responses.items():
            if key[: len(prefix)] == prefix:
                return subprocess.CompletedProcess(list(key), 0, stdout, "")
        raise AssertionError(f"unscripted call: {list(key)}")


PR_URL = "https://github.com/owner/repo/pull/42"
VIEW_RESPONSE = json.dumps({"number": 42, "url": PR_URL})


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


def _add_origin(root: Path) -> None:
    remote = root.parent / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    _git(root, "remote", "add", "origin", str(remote))


def _open(root: Path, client: GitHubClient) -> GitHubPRResult:
    return open_pull_request(
        root,
        "## Look\nProof packet body\n",
        client=client,
        poll_interval_s=1,
        timeout_s=10,
        sleep=lambda _seconds: None,
        monotonic=lambda: 0,
    )


def _fake_with(batches: list[tuple[GitHubCheck, ...]]) -> FakeGitHub:
    github = FakeGitHub()
    github.check_batches.extend(batches)
    return github


def _wait(
    github: FakeGitHub, *, timeout_s: float = 10, clock: Callable[[], float] | None = None
) -> tuple[tuple[GitHubCheck, ...], list[float]]:
    sleeps: list[float] = []
    checks = wait_for_checks(
        github,
        42,
        poll_interval_s=2,
        timeout_s=timeout_s,
        sleep=sleeps.append,
        monotonic=clock or (lambda: 0),
    )
    return checks, sleeps


def _ticking_clock(step: float) -> Callable[[], float]:
    now = [0.0]

    def clock() -> float:
        value = now[0]
        now[0] += step
        return value

    return clock


def test_github_pr_includes_proof_packet(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    github = _fake_with([(GitHubCheck("CI", "completed", "success"),)])

    result = _open(root, github)

    assert github.body == "## Look\nProof packet body\n"
    assert result.number == 42
    assert result.url.endswith("/pull/42")
    assert github.events[:2] == [
        "push:origin:phase/project-config",
        "create:phase/project-config:main:phase/project-config: phase proof",
    ]


def test_wait_polls_while_no_checks() -> None:
    github = _fake_with([(), (), (GitHubCheck("CI", "completed", "success"),)])

    checks, sleeps = _wait(github)

    assert checks == (GitHubCheck("CI", "completed", "success"),)
    assert sleeps == [2, 2]
    assert github.events == ["checks:42"] * 3


def test_wait_polls_while_incomplete() -> None:
    github = _fake_with(
        [
            (GitHubCheck("CI", "completed", "success"), GitHubCheck("Lint", "in_progress", None)),
            (
                GitHubCheck("CI", "completed", "success"),
                GitHubCheck("Lint", "completed", "success"),
            ),
        ]
    )

    checks, sleeps = _wait(github)

    assert all(check.status == "completed" for check in checks)
    assert sleeps == [2]


def test_wait_times_out_naming_pending() -> None:
    pending = (
        GitHubCheck("CI", "completed", "success"),
        GitHubCheck("Lint", "in_progress", None),
        GitHubCheck("Docs", "in_progress", None),
    )
    github = _fake_with([pending] * 20)

    with pytest.raises(TimeoutError, match=r"Lint, Docs") as raised:
        _wait(github, timeout_s=5, clock=_ticking_clock(2))

    assert "CI" not in str(raised.value).split("timeout:")[1]


def test_result_fail_on_bad_conclusion(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    github = _fake_with(
        [(GitHubCheck("CI", "completed", "success"), GitHubCheck("Lint", "completed", "failure"))]
    )

    result = _open(root, github)

    assert result.result == "fail"
    assert result.checks[1].conclusion == "failure"


def test_result_success_on_good_conclusions(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    github = _fake_with(
        [
            (
                GitHubCheck("CI", "completed", "success"),
                GitHubCheck("Lint", "completed", "neutral"),
                GitHubCheck("Docs", "completed", "skipped"),
            )
        ]
    )

    assert _open(root, github).result == "success"


def test_github_pr_waits_through_open_pull_request(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    github = _fake_with([(), (GitHubCheck("CI", "in_progress", None),)])
    github.check_batches.append((GitHubCheck("CI", "completed", "success"),))
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
    assert sleeps == [2, 2]


def test_github_pr_adapter_runs_through_dispatch_land(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    _add_origin(root)
    config_path = root / "orchestra.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8") + '\n[land.config]\nrepository = "owner/repo"\n',
        encoding="utf-8",
    )
    _git(root, "add", "orchestra.toml")
    _git(root, "commit", "-qm", "configure GitHub adapter")
    run = ScriptedGh(
        responses={
            ("gh", "pr", "create"): f"{PR_URL}\n",
            ("gh", "pr", "view"): VIEW_RESPONSE,
            ("gh", "pr", "checks"): json.dumps(
                [{"name": "CI", "state": "FAILURE", "bucket": "fail"}]
            ),
        }
    )
    configured: list[tuple[str, JsonObject]] = []
    real_gh = github_pr.GitHubGh

    def create_client(root: Path, remote: str, config: JsonObject | None) -> GitHubGh:
        configured.append((remote, config or {}))
        return real_gh(root, remote, config, run=run)

    monkeypatch.setattr(github_pr, "GitHubGh", create_client)

    result = dispatch_land(root, "proof packet", poll_interval_s=1, timeout_s=10)

    assert result.result == "fail"
    assert result.number == 42
    assert result.checks == (LandingCheck("CI", "completed", "failure"),)
    assert configured == [("origin", {"repository": "owner/repo"})]
    create = next(call for call in run.calls if call[:3] == ("gh", "pr", "create"))
    assert create[-2:] == ("-R", "owner/repo")


def test_adapter_statuses_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    _add_origin(root)
    run = ScriptedGh(
        responses={
            ("gh", "pr", "create"): f"{PR_URL}\n",
            ("gh", "pr", "view"): VIEW_RESPONSE,
            ("gh", "pr", "checks"): json.dumps(
                [{"name": "CI", "state": "SUCCESS", "bucket": "pass"}]
            ),
        }
    )
    real_gh = github_pr.GitHubGh
    monkeypatch.setattr(
        github_pr,
        "GitHubGh",
        lambda root, remote, config: real_gh(root, remote, config, run=run),
    )

    result = dispatch_land(root, "proof packet", poll_interval_s=1, timeout_s=10)

    assert result.result == "success"
    assert result.statuses == ()


def test_github_pr_never_merges(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    github = _fake_with([(GitHubCheck("CI", "completed", "success"),)])

    _open(root, github)

    assert all("merge" not in event for event in github.events)
    assert not hasattr(github, "merge")


def test_github_pr_refuses_non_human_merge(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    config_path = root / "orchestra.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace('merge = "human"', 'merge = "auto"'),
        encoding="utf-8",
    )
    _git(root, "add", "orchestra.toml")
    _git(root, "commit", "-qm", "auto merge")

    with pytest.raises(Exception, match="human"):
        _open(root, FakeGitHub())


def test_open_pull_request_without_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    _add_origin(root)
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    run = ScriptedGh(
        responses={
            ("gh", "pr", "create"): f"{PR_URL}\n",
            ("gh", "pr", "view"): VIEW_RESPONSE,
            ("gh", "pr", "checks"): json.dumps(
                [{"name": "CI", "state": "SUCCESS", "bucket": "pass"}]
            ),
        }
    )

    result = _open(root, GitHubGh(root, run=run))

    assert result.number == 42
    assert result.url == PR_URL
    assert result.result == "success"


def test_old_gh_fails_landing(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    _add_origin(root)

    with pytest.raises(GitHubPRError):
        _open(root, GitHubGh(root, run=ScriptedGh(version="gh version 2.4.0\n")))


def test_old_gh_error_names_versions(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    _add_origin(root)

    with pytest.raises(GitHubPRError) as raised:
        _open(root, GitHubGh(root, run=ScriptedGh(version="gh version 2.4.0\n")))

    assert "2.4.0" in str(raised.value)
    assert "2.50.0" in str(raised.value)


def test_failing_gh_raises_with_stderr(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    _add_origin(root)
    run = ScriptedGh(failures={("gh", "pr", "create"): (1, "GraphQL: base branch not found")})

    with pytest.raises(GitHubPRError, match="GraphQL: base branch not found"):
        _open(root, GitHubGh(root, run=run))


def test_missing_gh_raises(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    _add_origin(root)

    with pytest.raises(GitHubPRError, match="gh"):
        _open(root, GitHubGh(root, run=ScriptedGh(missing=True)))


def test_duplicate_pull_request_carries_url(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _write_project(root)
    _add_origin(root)
    stderr = f"a pull request for branch already exists:\n{PR_URL}\n"
    run = ScriptedGh(failures={("gh", "pr", "create"): (1, stderr)})

    with pytest.raises(GitHubPRError) as raised:
        _open(root, GitHubGh(root, run=run))

    assert PR_URL in str(raised.value)


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
        project_root = tmp_path

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
            statuses=(),
        )

    monkeypatch.setattr("orchestra.store.open_store", lambda _root, store=None: FakeProject())
    monkeypatch.setattr(cli.gate, "gate_terms", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(cli, "git_head", lambda _root: "head-sha")
    monkeypatch.setattr(cli.land, "dispatch_land", fake_open_pull_request)

    exit_code = cli.main(["land", "--phase", "project-config", "--cwd", str(tmp_path)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert '"url": "https://github.com/owner/repo/pull/42"' in output
    assert '"result": "success"' in output
