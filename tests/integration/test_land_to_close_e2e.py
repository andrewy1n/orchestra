"""A phase lands through `orchestra land`, then closes through `orchestra close` after the merge."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

import pytest
from conductor_support import PHASE, Cli, Phase, _packet, _review_repo_head, seed
from conftest import git

import orchestra.conductor.landing.github_pr as github_pr
from orchestra.canon.project import open_store
from orchestra.canon.types import Record
from orchestra.canon.workspace import Workspace
from orchestra.conductor.landing import land
from orchestra.conductor.phases.progress import close
from orchestra.tools import Version
from orchestra.tools.github import GitHubGh
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
                "--title", f"{PHASE} ({PHASE})", "--body-file", "-",
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


def _land(phase: Phase, tree: Path, run: ScriptedRun) -> land.LandingResult:
    return land.land_phase(
        Workspace(phase.store),
        PHASE,
        tree,
        GitHubGh(tree, "origin", {}, run=run),
        base="main",
        remote="origin",
        poll_interval_s=1,
        timeout_s=10,
    )


def test_merged_phase_closes_end_to_end(phase: Phase) -> None:
    tree, head = _landing_setup(phase)
    land_run = _land_run(head)
    _review_repo_head(phase)
    _packet(phase)

    assert _land(phase, tree, land_run).result == "success"

    create = next(call for call in land_run.calls if call[:3] == ("gh", "pr", "create"))
    assert create[-2:] == ("--body-file", "-")
    [record] = _landing_records(phase)
    assert record["payload"]["number"] == 7
    assert record["payload"]["result"] == "success"
    assert git(phase.repo, "ls-remote", "--heads", "origin", BRANCH).stdout.strip()

    merged_run = _merged_run(head)
    states = GitHubGh(phase.repo, "origin", {}, run=merged_run)
    project = open_store(phase.store)

    assert close.close_phase(
        project, phase.repo, PHASE, states, reconcile_architecture=lambda *_: False
    ).ready

    assert not tree.exists()
    assert not (phase.repo / ".worktrees" / f"{PHASE}--task").exists()
    assert git(phase.repo, "branch", "--list", BRANCH, f"task/{PHASE}/*").stdout.strip() == ""
    assert open_store(phase.store).resolve("score:phase", PHASE)["lifecycle_state"] == "done"
    assert close.close_phase(
        project, phase.repo, PHASE, states, reconcile_architecture=lambda *_: False
    ).ready
    assert merged_run.calls[-1] == ("gh", "pr", "view", "7", "--json", "state,headRefOid")


def test_land_and_close_use_gh_only(phase: Phase) -> None:
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
    _review_repo_head(phase)
    _packet(phase)
    assert _land(phase, tree, land_run).result == "success"
    merged_run = _merged_run(head)
    close.close_phase(
        open_store(phase.store),
        phase.repo,
        PHASE,
        GitHubGh(phase.repo, "origin", {}, run=merged_run),
        reconcile_architecture=lambda *_: False,
    )

    assert {call[0] for call in [*land_run.calls, *merged_run.calls]} == {"gh"}
