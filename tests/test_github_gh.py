from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from orchestra.conductor.github_pr import GitHubGh, GitHubPRError
from orchestra.tools import CliTool, Version
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
        self.inputs: list[tuple[tuple[str, ...], str | None]] = []

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        input: str | None,
        timeout: float,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
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
