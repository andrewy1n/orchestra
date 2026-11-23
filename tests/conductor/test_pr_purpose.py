"""The pull request carries the phase summary and proof without its diff."""

from __future__ import annotations

from pathlib import Path

from conductor_support import PHASE, Cli, Phase, _packet, _review_repo_head, seed
from test_land_sequence import FakeGh, land_through, use_adapter

from orchestra.canon.types import Record
from orchestra.conductor.landing.github_pr import open_pull_request
from orchestra.conductor.landing.landing import (
    describe_phase,
    pull_request_body,
    pull_request_title,
)
from orchestra.tools.github import GitHubCheck

BODY = (
    "## Problem\n\nThe loop ends at land.\n\n"
    "## Approach\n\nAdd a close step.\n\n"
    "## Exit criteria\n\n- Verify ends at the gate.\n- Close removes worktrees.\n\n"
    "## Proof\n\nkind: commands.\n\n## Landing\n\n- Branch: `phase/x`\n"
)
PACKET = "## Look\n\nRead the e2e output.\n\n## Machine\n\nhead abc\n\n## Attention\n\nnone\n\n## Diff\n\n1 file\n"


def _phase(body: str = BODY) -> Record:
    return {
        "id": "rec-phase",
        "record_type": "score:phase",
        "subject": "land-to-close",
        "payload": {"title": "Land through CI repair to close", "ordinal": 40, "effort": "e"},
        "lifecycle_state": "in_progress",
        "relationships": {},
        "revision": "sha256:x",
        "recorded_at": "2026-11-08T10:00:00+00:00",
        "body": body,
    }


def _body() -> str:
    return pull_request_body(describe_phase(_phase()), PACKET)


def test_title_is_the_phase_title_and_slug() -> None:
    assert pull_request_title(_phase()) == "Land through CI repair to close (land-to-close)"


def test_description_starts_with_the_purpose() -> None:
    assert _body().startswith("## What this PR is for\n\nThe loop ends at land.\n")


def test_description_gives_the_approach() -> None:
    assert "\n## Approach\n\nAdd a close step.\n" in _body()


def test_description_lists_the_exit_criteria() -> None:
    assert (
        "\n## Exit criteria\n\n- Verify ends at the gate.\n- Close removes worktrees.\n" in _body()
    )


def test_description_includes_proof_without_the_redundant_diff() -> None:
    body = _body()

    assert "## Proof packet" in body
    assert "### Look\n\nRead the e2e output." in body
    assert "### Machine\n\nhead abc" in body
    assert "### Attention\n\nnone" in body
    assert "### Diff" not in body
    assert "1 file" not in body


def test_a_phase_without_sections_still_includes_the_proof_packet() -> None:
    bare = _phase("no sections here\n")

    body = pull_request_body(describe_phase(bare), PACKET)

    assert pull_request_title(bare) == "Land through CI repair to close (land-to-close)"
    assert "## Proof packet" in body
    assert "### Look" in body
    assert "### Diff" not in body


class Recorder:
    def __init__(self, head: str, existing: tuple[int, str] | None = None) -> None:
        self.head = head
        self.existing = existing
        self.title = ""
        self.body = ""
        self.created = False
        self.updates: list[tuple[int, str, str]] = []

    def push_branch(self, remote: str, branch: str) -> None:
        del remote, branch

    def find_pull_request(self, head: str) -> tuple[int, str] | None:
        del head
        return self.existing

    def update_pull_request(self, number: int, title: str, body: str) -> None:
        self.updates.append((number, title, body))

    def create_pull_request(self, head: str, base: str, title: str, body: str) -> tuple[int, str]:
        del head, base
        self.title, self.body = title, body
        self.created = True
        return 7, "https://github.com/o/r/pull/7"

    def head_sha(self, number: int) -> str:
        del number
        return self.head

    def checks(self, number: int) -> tuple[GitHubCheck, ...]:
        del number
        return (GitHubCheck("CI", "completed", "success"),)


def test_open_pull_request_sends_the_title_and_the_description(tmp_path: Path) -> None:
    from test_pr_reuse import _git, _repo

    root = _repo(tmp_path)
    client = Recorder(_git(root, "rev-parse", "HEAD"))

    open_pull_request(
        root,
        PACKET,
        title=pull_request_title(_phase()),
        description=describe_phase(_phase()),
        client=client,
        poll_interval_s=1,
        timeout_s=10,
        sleep=lambda _seconds: None,
        monotonic=lambda: 0,
    )

    assert client.title == "Land through CI repair to close (land-to-close)"
    assert client.body == _body()


def test_land_sends_the_phase_title_and_purpose_to_the_pull_request(store: Path, cli: Cli) -> None:
    phase: Phase = seed(store, cli)
    use_adapter(phase, "github-pr")
    _review_repo_head(phase)
    _packet(phase)
    gh = FakeGh()

    land_through(phase, gh)

    [(title, body)] = gh.created
    assert title == f"{PHASE} ({PHASE})"
    assert "## What this PR is for\n\np\n" in body
    assert "## Approach\n\na\n" in body
    assert "## Exit criteria\n\ne\n" in body


def _rerun(tmp_path: Path) -> Recorder:
    from test_pr_reuse import _git, _repo

    root = _repo(tmp_path)
    client = Recorder(
        _git(root, "rev-parse", "HEAD"), existing=(7, "https://github.com/o/r/pull/7")
    )
    open_pull_request(
        root,
        PACKET,
        title=pull_request_title(_phase()),
        description=describe_phase(_phase()),
        client=client,
        poll_interval_s=1,
        timeout_s=10,
        sleep=lambda _seconds: None,
        monotonic=lambda: 0,
    )
    return client


def test_rerun_updates_the_pull_request_title(tmp_path: Path) -> None:
    client = _rerun(tmp_path)

    assert not client.created
    assert [(number, title) for number, title, _body in client.updates] == [
        (7, "Land through CI repair to close (land-to-close)")
    ]


def test_rerun_updates_the_pull_request_description(tmp_path: Path) -> None:
    client = _rerun(tmp_path)

    assert [body for _number, _title, body in client.updates] == [_body()]


def test_gh_edit_updates_the_title_and_the_description(tmp_path: Path) -> None:
    from orchestra.tools.github import GitHubGh
    from orchestra.tools.testing import scripted

    argv = ("gh", "pr", "edit", "7", "--title", "T", "--body-file", "-")
    run = scripted(GitHubGh, {argv: ""})

    GitHubGh(tmp_path, run=run).update_pull_request(7, "T", "the body")

    assert run.calls[-1] == argv
