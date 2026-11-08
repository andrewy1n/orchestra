"""`orchestra close`: act on a landed phase only after its pull request merges."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from orchestra.canon import record_payload
from orchestra.canon.project import Project
from orchestra.canon.project_config import load_project_config
from orchestra.conductor.github_pr import GitHubGh
from orchestra.conductor.landing import latest_landing
from orchestra.tools import Git, ToolError


class CloseError(RuntimeError):
    """The phase cannot be assessed for close; the message names what to fix."""


class PullRequestStates(Protocol):
    def pull_request_state(self, number: int) -> tuple[str, str]: ...


@dataclass(frozen=True)
class CloseResult:
    phase: str
    number: int
    url: str
    state: str
    head_sha: str
    ready: bool
    refusals: tuple[str, ...]
    message: str


def primary_checkout(cwd: Path) -> Path:
    common = Git(cwd).text("rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common).parent


def github_states(repo: Path) -> PullRequestStates:
    return GitHubGh(repo, "origin", load_project_config(repo).land_config)


def close_phase(project: Project, repo: Path, phase: str, states: PullRequestStates) -> CloseResult:
    landing = latest_landing(project.list("conductor:landing"), phase)
    if landing is None:
        raise CloseError(f"no landing record for phase {phase!r}; run orchestra land first")
    landed = record_payload(landing)
    number = landed.get("number")
    url = landed.get("url")
    if isinstance(number, bool) or not isinstance(number, int) or not isinstance(url, str):
        raise CloseError(f"the landing record for phase {phase!r} has no pull request")
    state, head_sha = states.pull_request_state(number)
    if state != "MERGED":
        message = f"pull request {number} is {state}; close waits for the merge"
        return CloseResult(phase, number, url, state, head_sha, False, (), message)
    refusals = _refusals(repo, phase, head_sha)
    if refusals:
        message = f"pull request {number} is MERGED; close refused"
    else:
        message = f"pull request {number} is MERGED; close can proceed"
    return CloseResult(phase, number, url, state, head_sha, not refusals, refusals, message)


def phase_worktree(repo: Path, phase: str) -> Path:
    return repo / ".worktrees" / phase


def task_worktrees(repo: Path, phase: str) -> tuple[Path, ...]:
    root = repo / ".worktrees"
    if not root.is_dir():
        return ()
    return tuple(sorted(path for path in root.glob(f"{phase}--*") if path.is_dir()))


def _refusals(repo: Path, phase: str, head_sha: str) -> tuple[str, ...]:
    refusals: list[str] = []
    trees = [phase_worktree(repo, phase), *task_worktrees(repo, phase)]
    for tree in trees:
        if tree.is_dir() and Git(tree).status_porcelain():
            refusals.append(f"worktree {tree} has uncommitted changes")
    git = Git(repo)
    phase_branch = f"phase/{phase}"
    tip = git.branch_tip(phase_branch)
    if tip is not None and tip != head_sha:
        refusals.append(
            f"branch {phase_branch} tip {tip[:12]} differs from "
            f"the merged pull request head {head_sha[:12]}"
        )
    reference = tip or head_sha
    for branch in git.branches(f"task/{phase}/"):
        task_tip = git.branch_tip(branch)
        if task_tip is None:
            continue
        try:
            contained = git.is_ancestor(task_tip, reference)
        except ToolError as error:
            refusals.append(f"branch {branch} cannot be checked against {phase_branch}: {error}")
            continue
        if not contained:
            refusals.append(f"branch {branch} has commits not in {phase_branch}")
    return tuple(refusals)
