from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, overload

import pytest

import orchestra.conductor.github_pr as github_pr
from orchestra.conductor.github_pr import GitHubCheck, GitHubGh, GitHubPRError
from orchestra.tools import CliTool, Git, ToolError, Version
from orchestra.tools.testing import scripted

URL = "https://github.com/acme/widgets/pull/7"
VIEW = json.dumps({"number": 7, "url": URL})
CREATE = (
    "gh",
    "pr",
    "create",
    "--base",
    "main",
    "--head",
    "feat",
    "--title",
    "T",
    "--body-file",
    "-",
)
VIEW_ARGV = ("gh", "pr", "view", URL, "--json", "number,url")


class RecordingRun:
    def __init__(self) -> None:
        self.inputs: list[tuple[tuple[str, ...], str | bytes | None]] = []

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
        key = tuple(argv)
        self.inputs.append((key, input))
        if key[1:] == ("--version",):
            stdout = "gh version 2.50.0 (2024-06-01)\n"
        elif key[:3] == ("gh", "pr", "create"):
            stdout = f"Creating pull request\n{URL}\n"
        else:
            stdout = VIEW
        return subprocess.CompletedProcess(list(key), 0, stdout, "")


def test_gh_runs_through_cli_tool(tmp_path: Path) -> None:
    assert issubclass(GitHubGh, CliTool)
    assert GitHubGh.executable == "gh"
    run = scripted(GitHubGh, {VIEW_ARGV: VIEW})
    gh = GitHubGh(tmp_path, run=run)
    assert gh.pull_request(URL) == (7, URL)
    assert run.calls[0] == ("gh", "--version")


def test_min_version_is_2_50() -> None:
    assert GitHubGh.min_version == Version(2, 50, 0)


def test_create_pull_request_flags(tmp_path: Path) -> None:
    run = scripted(GitHubGh, {CREATE: f"{URL}\n", VIEW_ARGV: VIEW})
    GitHubGh(tmp_path, run=run).create_pull_request("feat", "main", "T", "B")
    assert CREATE in run.calls


def test_create_pull_request_body_on_stdin(tmp_path: Path) -> None:
    run = RecordingRun()
    GitHubGh(tmp_path, run=run).create_pull_request("feat", "main", "T", "the body")
    assert (CREATE, "the body") in run.inputs


def test_create_pull_request_reads_number_with_view(tmp_path: Path) -> None:
    run = scripted(GitHubGh, {CREATE: f"noise\n{URL}\n\n", VIEW_ARGV: VIEW})
    GitHubGh(tmp_path, run=run).create_pull_request("feat", "main", "T", "B")
    assert run.calls[-1] == VIEW_ARGV


def test_create_pull_request_returns_number_and_url(tmp_path: Path) -> None:
    run = scripted(GitHubGh, {CREATE: f"{URL}\n", VIEW_ARGV: VIEW})
    assert GitHubGh(tmp_path, run=run).create_pull_request("feat", "main", "T", "B") == (7, URL)


def test_repository_flag_when_configured(tmp_path: Path) -> None:
    create = (*CREATE, "-R", "acme/widgets")
    view = (*VIEW_ARGV, "-R", "acme/widgets")
    run = scripted(GitHubGh, {create: f"{URL}\n", view: VIEW})
    gh = GitHubGh(tmp_path, adapter_config={"repository": "acme/widgets"}, run=run)
    assert gh.create_pull_request("feat", "main", "T", "B") == (7, URL)
    assert create in run.calls
    assert view in run.calls


def test_no_repository_flag_when_unset(tmp_path: Path) -> None:
    run = scripted(GitHubGh, {CREATE: f"{URL}\n", VIEW_ARGV: VIEW})
    GitHubGh(tmp_path, run=run).create_pull_request("feat", "main", "T", "B")
    assert all("-R" not in call for call in run.calls)


@pytest.mark.parametrize("repository", ["widgets", "a/b/c", "/b", "a/", "", 3])
def test_invalid_repository_raises(tmp_path: Path, repository: str | int) -> None:
    with pytest.raises(GitHubPRError, match="owner/repository"):
        GitHubGh(tmp_path, adapter_config={"repository": repository})


CHECKS_ARGV = ("gh", "pr", "checks", "7", "--json", "name,state,bucket")


def _checks(bucket: str) -> str:
    return json.dumps([{"name": "ci", "state": "X", "bucket": bucket}])


class FailingChecksRun:
    def __init__(self, stderr: str) -> None:
        self.stderr = stderr

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
        key = tuple(argv)
        if key == ("gh", "--version"):
            return subprocess.CompletedProcess(list(key), 0, "gh version 2.50.0\n", "")
        return subprocess.CompletedProcess(list(key), 1, "", self.stderr)


def test_checks_command(tmp_path: Path) -> None:
    run = scripted(GitHubGh, {CHECKS_ARGV: _checks("pass")})
    GitHubGh(tmp_path, run=run).checks(7)
    assert CHECKS_ARGV in run.calls


def test_checks_repository_flag(tmp_path: Path) -> None:
    argv = (*CHECKS_ARGV, "-R", "acme/widgets")
    run = scripted(GitHubGh, {argv: _checks("pass")})
    gh = GitHubGh(tmp_path, adapter_config={"repository": "acme/widgets"}, run=run)
    assert len(gh.checks(7)) == 1


def _one(tmp_path: Path, bucket: str) -> tuple[GitHubCheck, ...]:
    run = scripted(GitHubGh, {CHECKS_ARGV: _checks(bucket)})
    return GitHubGh(tmp_path, run=run).checks(7)


def test_bucket_pass_maps_to_success(tmp_path: Path) -> None:
    assert _one(tmp_path, "pass") == (GitHubCheck("ci", "completed", "success"),)


def test_bucket_fail_maps_to_failure(tmp_path: Path) -> None:
    assert _one(tmp_path, "fail") == (GitHubCheck("ci", "completed", "failure"),)


def test_bucket_pending_maps_to_in_progress(tmp_path: Path) -> None:
    assert _one(tmp_path, "pending") == (GitHubCheck("ci", "in_progress", None),)


def test_bucket_skipping_maps_to_skipped(tmp_path: Path) -> None:
    assert _one(tmp_path, "skipping") == (GitHubCheck("ci", "completed", "skipped"),)


def test_bucket_cancel_maps_to_cancelled(tmp_path: Path) -> None:
    assert _one(tmp_path, "cancel") == (GitHubCheck("ci", "completed", "cancelled"),)


def test_unknown_bucket_raises(tmp_path: Path) -> None:
    with pytest.raises(GitHubPRError, match="bucket"):
        _one(tmp_path, "weird")


@pytest.mark.parametrize(
    "output",
    ['{"name": "ci"}', '["ci"]', '[{"name": "ci"}]', '[{"name": 1, "bucket": "pass"}]'],
)
def test_non_list_output_raises(tmp_path: Path, output: str) -> None:
    run = scripted(GitHubGh, {CHECKS_ARGV: output})
    with pytest.raises(GitHubPRError):
        GitHubGh(tmp_path, run=run).checks(7)


def test_empty_list_returns_no_checks(tmp_path: Path) -> None:
    run = scripted(GitHubGh, {CHECKS_ARGV: "[]"})
    assert GitHubGh(tmp_path, run=run).checks(7) == ()


def test_no_checks_reported_returns_no_checks(tmp_path: Path) -> None:
    stderr = "no checks reported on the 'feat' branch\n"
    assert GitHubGh(tmp_path, run=FailingChecksRun(stderr)).checks(7) == ()


def test_other_tool_error_is_not_swallowed(tmp_path: Path) -> None:
    with pytest.raises(ToolError):
        GitHubGh(tmp_path, run=FailingChecksRun("HTTP 502")).checks(7)


def test_push_branch_runs_git_push_through_git_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    push = ("git", "push", "--set-upstream", "origin", "branch")
    run = scripted(Git, {push: ""})
    monkeypatch.setattr(github_pr, "Git", lambda root: Git(root, run=run))
    gh_run = scripted(GitHubGh, {})
    GitHubGh(tmp_path, run=gh_run).push_branch("origin", "branch")
    assert run.calls == [("git", "--version"), push]


def test_push_branch_reports_timeout_cause(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def timing_out(argv: Sequence[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if list(argv)[1:] == ["--version"]:
            return subprocess.CompletedProcess(list(argv), 0, "git version 2.40.0\n", "")
        raise subprocess.TimeoutExpired(list(argv), 5.0)

    monkeypatch.setattr(github_pr, "Git", lambda root: Git(root, run=timing_out))  # pyright: ignore[reportArgumentType]
    gh_run = scripted(GitHubGh, {})
    with pytest.raises(GitHubPRError) as info:
        GitHubGh(tmp_path, run=gh_run).push_branch("origin", "branch")
    assert "timed out" in str(info.value)
    assert "not found" not in str(info.value)
