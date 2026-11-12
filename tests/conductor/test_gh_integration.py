from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from orchestra.conductor.github_pr import GitHubGh

PUBLIC_REPOSITORY = "cli/cli"
PUBLIC_PULL_REQUEST = 9079


def _require_authenticated_gh() -> None:
    if shutil.which("gh") is None:
        pytest.skip("gh is not on PATH")
    status = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, check=False)
    if status.returncode != 0:
        pytest.skip("gh is not authenticated")


def _client(tmp_path: Path) -> GitHubGh:
    _require_authenticated_gh()
    return GitHubGh(tmp_path, adapter_config={"repository": PUBLIC_REPOSITORY})


def test_real_gh_pr_view_reads_public_pull_request(tmp_path: Path) -> None:
    client = _client(tmp_path)

    assert client.pull_request(str(PUBLIC_PULL_REQUEST)) == (
        PUBLIC_PULL_REQUEST,
        f"https://github.com/{PUBLIC_REPOSITORY}/pull/{PUBLIC_PULL_REQUEST}",
    )


def test_real_gh_reports_no_checks_for_public_pull_request(tmp_path: Path) -> None:
    client = _client(tmp_path)

    assert client.checks(PUBLIC_PULL_REQUEST) == ()
