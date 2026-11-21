from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from conductor_support import PHASE, Cli, Phase, _land_args, _packet, _review_repo_head, seed
from conftest import git

from orchestra.canon.types import Record
from orchestra.canon.workspace import Workspace
from orchestra.cli import main as cli_main
from orchestra.conductor import land
from orchestra.conductor.github_pr import GitHubCheck, GitHubPRError
from orchestra.tools import Git

URL = "https://github.com/owner/repo/pull/7"


@dataclass
class FakeGh:
    conclusion: str = "success"
    head: str = ""
    pushed: list[str] = field(default_factory=lambda: [])
    created: list[tuple[str, str]] = field(default_factory=lambda: [])

    def push_branch(self, remote: str, branch: str) -> None:
        self.pushed.append(f"{remote}:{branch}")

    def find_pull_request(self, head: str) -> tuple[int, str] | None:
        return None

    def create_pull_request(self, head: str, base: str, title: str, body: str) -> tuple[int, str]:
        self.created.append((title, body))
        return 7, URL

    def update_pull_request(self, number: int, title: str, body: str) -> None:
        raise AssertionError("no pull request exists to update")

    def head_sha(self, number: int) -> str:
        return self.head

    def checks(self, number: int) -> tuple[GitHubCheck, ...]:
        return (GitHubCheck("CI", "completed", self.conclusion),)


@pytest.fixture
def phase(store: Path, cli: Cli) -> Phase:
    return seed(store, cli)


def use_adapter(phase: Phase, adapter: str) -> None:
    with (phase.repo / "orchestra.toml").open("a", encoding="utf-8") as policy:
        policy.write(f'\n[land]\nadapter = "{adapter}"\nmerge = "human"\n')
    git(phase.repo, "add", "orchestra.toml")
    git(phase.repo, "commit", "-qm", "land policy")


def land_through(phase: Phase, gh: FakeGh) -> land.LandingResult:
    gh.head = Git(phase.repo).head()
    return land.land_phase(
        Workspace(phase.store),
        PHASE,
        phase.repo,
        gh,
        base="main",
        remote="origin",
        poll_interval_s=1,
        timeout_s=10,
    )


def _landing_records(phase: Phase) -> list[Record]:
    result = phase.cli("list", "--type", "conductor:landing", "--subject", PHASE)
    assert result.returncode == 0, result.stdout + result.stderr
    records: list[Record] = json.loads(result.stdout)["records"]
    return records


def _packet_at(phase: Phase, revision: str) -> None:
    phase.create(
        "conductor:proof-packet",
        PHASE,
        {
            "phase": PHASE,
            "effort": "gate-effort",
            "revision": revision,
            "base": "main",
            "kind": "claims",
        },
        "## Look\nl\n\n## Machine\nm\n\n## Attention\nnone\n\n## Diff\n1 file changed\n",
    )


def test_r16_selects_the_packet_at_the_worktree_head(phase: Phase) -> None:
    use_adapter(phase, "github-pr")
    head = _review_repo_head(phase)
    _packet(phase)

    result = land_through(phase, FakeGh())

    assert result.result == "success"
    assert head


def test_r16_accepts_a_packet_recorded_at_a_seven_character_head_prefix(phase: Phase) -> None:
    use_adapter(phase, "github-pr")
    head = _review_repo_head(phase)
    _packet_at(phase, head[:7])

    result = land_through(phase, FakeGh())

    assert result.result == "success"
    assert result.number == 7


def test_r16_refuses_when_no_packet_matches_the_head(phase: Phase) -> None:
    use_adapter(phase, "github-pr")
    _review_repo_head(phase)
    _packet_at(phase, "f" * 40)
    gh = FakeGh()

    with pytest.raises(ValueError, match="no proof packet"):
        land_through(phase, gh)

    assert gh.pushed == []


def test_r16_cli_exits_two_when_no_packet_matches(
    phase: Phase, capsys: pytest.CaptureFixture[str]
) -> None:
    use_adapter(phase, "github-pr")
    _review_repo_head(phase)

    assert cli_main(_land_args(phase)) == 2
    assert "no proof packet" in capsys.readouterr().err


def test_r17_records_the_landing_after_a_successful_run(phase: Phase) -> None:
    use_adapter(phase, "github-pr")
    head = _review_repo_head(phase)
    _packet(phase)

    land_through(phase, FakeGh())

    [record] = _landing_records(phase)
    assert record["payload"] == {
        "phase": PHASE,
        "number": 7,
        "url": URL,
        "head_sha": head,
        "result": "success",
        "effort": "gate-effort",
    }


def test_r17_records_the_landing_when_checks_fail(phase: Phase) -> None:
    use_adapter(phase, "github-pr")
    _review_repo_head(phase)
    _packet(phase)

    result = land_through(phase, FakeGh(conclusion="failure"))

    assert result.result == "fail"
    [record] = _landing_records(phase)
    assert record["payload"]["result"] == "fail"
    assert record["payload"]["number"] == 7


def test_r17_each_run_adds_one_record(phase: Phase) -> None:
    use_adapter(phase, "github-pr")
    _review_repo_head(phase)
    _packet(phase)

    land_through(phase, FakeGh(conclusion="failure"))
    land_through(phase, FakeGh())

    results = sorted(str(record["payload"]["result"]) for record in _landing_records(phase))
    assert results == ["fail", "success"]


def test_r17_a_skipped_result_writes_no_record(phase: Phase) -> None:
    use_adapter(phase, "none")
    _review_repo_head(phase)
    _packet(phase)

    result = land_through(phase, FakeGh())

    assert result.result == "skipped"
    assert _landing_records(phase) == []


def test_r17_a_failed_gate_raises_and_writes_no_record(phase: Phase) -> None:
    use_adapter(phase, "github-pr")
    _packet(phase)
    phase.finding()
    gh = FakeGh()

    with pytest.raises(land.LandGateError) as raised:
        land_through(phase, gh)

    assert any("finding-needs-human" in line for line in raised.value.lines)
    assert gh.pushed == []
    assert _landing_records(phase) == []


def test_r17_cli_exits_five_when_the_gate_fails(
    phase: Phase, capsys: pytest.CaptureFixture[str]
) -> None:
    _packet(phase)
    phase.finding()

    assert cli_main(_land_args(phase)) == 5
    assert "finding-needs-human" in capsys.readouterr().err
    assert _landing_records(phase) == []


def test_r17_an_adapter_error_writes_no_record(phase: Phase) -> None:
    use_adapter(phase, "github-pr")
    _review_repo_head(phase)
    _packet(phase)
    (phase.repo / "dirty.txt").write_text("x", encoding="utf-8")

    with pytest.raises(GitHubPRError, match="clean"):
        land_through(phase, FakeGh())

    assert _landing_records(phase) == []


def test_r17_proceeds_after_a_canon_only_commit(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, review=False, runner_check=False, prose_landing=True)
    use_adapter(phase, "github-pr")
    _review_repo_head(phase)
    (phase.repo / ".canon").mkdir()
    (phase.repo / ".canon" / "config.json").write_text("{}", encoding="utf-8")
    git(phase.repo, "add", ".canon/config.json")
    git(phase.repo, "commit", "-qm", "canon metadata")
    _packet(phase)

    result = land_through(phase, FakeGh())

    assert result.result == "success"
    assert len(_landing_records(phase)) == 1
