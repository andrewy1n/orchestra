"""A phase lands through `orchestra land`, then closes through `orchestra close` after the merge."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

import pytest
from conftest import git
from test_gate import PHASE, Cli, Phase, _packet, _review_repo_head, seed

import orchestra.conductor.github_pr as github_pr
from orchestra.canon.project import open_store
from orchestra.canon.types import Record
from orchestra.cli import main as cli_main
from orchestra.conductor import close
from orchestra.conductor.github_pr import GitHubGh
from orchestra.tools import Version
from orchestra.tools.testing import ScriptedRun, scripted

URL = "https://github.com/o/r/pull/7"
BRANCH = f"phase/{PHASE}"
LAND_POLICY = '\n[land]\nadapter = "github-pr"\nmerge = "human"\n'


@pytest.fixture
def phase(store: Path, cli: Cli) -> Phase:
    return seed(store, cli)


def _landing_setup(phase: Phase) -> tuple[Path, str]:
    repo = phase.repo
    origin = repo.parent / f"{repo.name}-origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    git(repo, "remote", "add", "origin", str(origin))
    with (repo / "orchestra.toml").open("a", encoding="utf-8") as policy:
        policy.write(LAND_POLICY)
    git(repo, "add", "orchestra.toml")
    git(repo, "commit", "-qm", "land policy")
    tree = repo / ".worktrees" / PHASE
    git(repo, "worktree", "add", "-q", "-b", BRANCH, str(tree), "main")
    task_tree = repo / ".worktrees" / f"{PHASE}--task"
    git(repo, "worktree", "add", "-q", "-b", f"task/{PHASE}/task", str(task_tree), BRANCH)
    head = git(tree, "rev-parse", "HEAD").stdout.strip()
    return tree, head


def _head_json(head: str) -> str:
    return json.dumps({"headRefOid": head})


def _land_run(head: str) -> ScriptedRun:
    return scripted(
        GitHubGh,
        {
            ("gh", "pr", "list", "--head", BRANCH, "--state", "open", "--json", "number,url"): "[]",
            (
                "gh", "pr", "create", "--base", "main", "--head", BRANCH,
                "--title", f"{BRANCH}: phase proof", "--body-file", "-",
            ): f"{URL}\n",
            ("gh", "pr", "view", URL, "--json", "number,url"): json.dumps(
                {"number": 7, "url": URL}
            ),
            ("gh", "pr", "view", "7", "--json", "headRefOid"): _head_json(head),
            ("gh", "pr", "checks", "7", "--json", "name,state,bucket"): json.dumps(
                [{"name": "CI", "state": "SUCCESS", "bucket": "pass"}]
            ),
        },
    )  # fmt: skip


def _merged_run(head: str) -> ScriptedRun:
    argv = ("gh", "pr", "view", "7", "--json", "state,headRefOid")
    return scripted(
        GitHubGh,
        {argv: json.dumps({"state": "MERGED", "headRefOid": head})},
        version=Version(2, 50),
    )


def _landing_records(phase: Phase) -> list[Record]:
    result = phase.cli("list", "--type", "conductor:landing", "--subject", PHASE)
    assert result.returncode == 0, result.stdout + result.stderr
    records: list[Record] = json.loads(result.stdout)["records"]
    return records


def test_merged_phase_closes_end_to_end(phase: Phase, monkeypatch: pytest.MonkeyPatch) -> None:
    tree, head = _landing_setup(phase)
    land_run = _land_run(head)
    real_gh = GitHubGh
    monkeypatch.setattr(
        github_pr,
        "GitHubGh",
        lambda root, remote, config: real_gh(root, remote, config, run=land_run),
    )
    _review_repo_head(phase)
    _packet(phase)
    land_args = ["land", "--phase", PHASE, "--cwd", str(tree), "--store", str(phase.store)]

    assert cli_main(land_args) == 0

    create = next(call for call in land_run.calls if call[:3] == ("gh", "pr", "create"))
    assert create[-2:] == ("--body-file", "-")
    [record] = _landing_records(phase)
    assert record["payload"]["number"] == 7
    assert record["payload"]["result"] == "success"
    assert git(phase.repo, "ls-remote", "--heads", "origin", BRANCH).stdout.strip()

    merged_run = _merged_run(head)
    monkeypatch.setattr(
        close,
        "github_states",
        lambda root: real_gh(root, "origin", {}, run=merged_run),
    )
    close_args = ["close", "--phase", PHASE, "--cwd", str(phase.repo), "--store", str(phase.store)]

    assert cli_main(close_args) == 0

    assert not tree.exists()
    assert not (phase.repo / ".worktrees" / f"{PHASE}--task").exists()
    assert git(phase.repo, "branch", "--list", BRANCH, f"task/{PHASE}/*").stdout.strip() == ""
    assert open_store(phase.store).resolve("score:phase", PHASE)["lifecycle_state"] == "done"
    assert cli_main(close_args) == 0
    assert merged_run.calls[-1] == ("gh", "pr", "view", "7", "--json", "state,headRefOid")


def test_land_and_close_use_gh_only(phase: Phase, monkeypatch: pytest.MonkeyPatch) -> None:
    banned = {"urllib", "requests", "httpx", "http", "socket", "aiohttp"}
    for module in (close, github_pr):
        source = Path(module.__file__ or "").read_text(encoding="utf-8")
        found = {
            alias.name.split(".")[0]
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module.split(".")[0]
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert not found & banned, (module.__name__, found & banned)

    tree, head = _landing_setup(phase)
    land_run = _land_run(head)
    monkeypatch.setattr(
        github_pr,
        "GitHubGh",
        lambda root, remote, config: GitHubGh(root, remote, config, run=land_run),
    )
    _review_repo_head(phase)
    _packet(phase)
    assert (
        cli_main(["land", "--phase", PHASE, "--cwd", str(tree), "--store", str(phase.store)]) == 0
    )
    merged_run = _merged_run(head)
    close.close_phase(
        open_store(phase.store),
        phase.repo,
        PHASE,
        GitHubGh(phase.repo, "origin", {}, run=merged_run),
    )

    assert {call[0] for call in [*land_run.calls, *merged_run.calls]} == {"gh"}
