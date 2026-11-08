"""`orchestra close`: act on a landed phase only after its pull request merges."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from orchestra.canon import record_payload
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.project_config import load_project_config
from orchestra.canon.types import Record
from orchestra.conductor.github_pr import GitHubGh
from orchestra.conductor.landing import LANDING, latest_landing
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
    actions: tuple[str, ...] = ()


def primary_checkout(cwd: Path) -> Path:
    common = Git(cwd).text("rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common).parent


def github_states(repo: Path) -> PullRequestStates:
    return GitHubGh(repo, "origin", load_project_config(repo).land_config)


def close_phase(
    project: Project,
    repo: Path,
    phase: str,
    states: PullRequestStates,
    cwd: Path | None = None,
) -> CloseResult:
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
    refusals = _refusals(repo, phase, head_sha, cwd)
    if refusals:
        message = f"pull request {number} is MERGED; close refused"
        return CloseResult(phase, number, url, state, head_sha, False, refusals, message)
    actions = _apply(project, repo, phase, number, head_sha)
    if actions:
        message = f"pull request {number} is MERGED; phase {phase} closed"
    else:
        message = f"pull request {number} is MERGED; phase {phase} has nothing left to do"
    return CloseResult(phase, number, url, state, head_sha, True, (), message, actions)


def landed_phases(project: Project) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for record in project.list(LANDING):
        phase = record_payload(record).get("phase")
        if isinstance(phase, str) and phase:
            seen.setdefault(phase)
    return tuple(seen)


def pending_close(project: Project, repo: Path, phase: str) -> bool:
    if project.resolve("score:phase", phase)["lifecycle_state"] != "done":
        return True
    if phase_worktree(repo, phase).is_dir() or task_worktrees(repo, phase):
        return True
    git = Git(repo)
    return git.branch_tip(f"phase/{phase}") is not None or bool(git.branches(f"task/{phase}/"))


def close_all(
    project: Project, repo: Path, states: PullRequestStates, cwd: Path | None = None
) -> tuple[CloseResult | str, ...]:
    """Close every landed phase that still has work to close; a failure becomes a message."""
    results: list[CloseResult | str] = []
    for phase in landed_phases(project):
        try:
            if not pending_close(project, repo, phase):
                continue
            results.append(close_phase(project, repo, phase, states, cwd))
        except (CloseError, StoreError, ToolError, RuntimeError, OSError, ValueError) as error:
            results.append(f"{phase}: {error}")
    return tuple(results)


def phase_worktree(repo: Path, phase: str) -> Path:
    return repo / ".worktrees" / phase


def task_worktrees(repo: Path, phase: str) -> tuple[Path, ...]:
    root = repo / ".worktrees"
    if not root.is_dir():
        return ()
    return tuple(sorted(path for path in root.glob(f"{phase}--*") if path.is_dir()))


def _refusals(repo: Path, phase: str, head_sha: str, cwd: Path | None) -> tuple[str, ...]:
    refusals: list[str] = []
    trees = [phase_worktree(repo, phase), *task_worktrees(repo, phase)]
    here = cwd.resolve() if cwd is not None else None
    for tree in trees:
        if not tree.is_dir():
            continue
        if here is not None and (here == tree.resolve() or tree.resolve() in here.parents):
            refusals.append(
                f"worktree {tree} holds the current directory {here}; "
                "run close from the main checkout"
            )
        if Git(tree).status_porcelain():
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


_TRANSITIONS = {"planned": ("in_progress", "done"), "in_progress": ("done",)}


def _apply(project: Project, repo: Path, phase: str, number: int, head_sha: str) -> tuple[str, ...]:
    git = Git(repo)
    actions: list[str] = []
    trees = [*task_worktrees(repo, phase), phase_worktree(repo, phase)]
    for tree in trees:
        if tree.is_dir():
            git.remove_worktree(tree)
            actions.append(f"removed worktree {tree}")
    for branch in git.branches(f"task/{phase}/"):
        git.delete_branch(branch)
        actions.append(f"deleted branch {branch}")
    phase_branch = f"phase/{phase}"
    if git.branch_tip(phase_branch) is not None:
        git.delete_branch(phase_branch)
        actions.append(f"deleted branch {phase_branch}")
    record = project.resolve("score:phase", phase)
    steps = _TRANSITIONS.get(record["lifecycle_state"], ())
    if not steps:
        return tuple(actions)
    effort = record_payload(record).get("effort")
    if isinstance(effort, str) and effort:
        actions.extend(_update_effort_position(project, effort, phase, number, head_sha))
    actions.extend(_close_phase_position(project, phase))
    for step in steps:
        record = project.update(record["id"], transition=step)
    actions.append(f"closed phase {phase}")
    return tuple(actions)


def _find_position(project: Project, subject: str, scope: str) -> Record | None:
    try:
        position = project.resolve("score:position", subject)
    except StoreError:
        return None
    return position if record_payload(position).get("scope") == scope else None


def _update_effort_position(
    project: Project, effort: str, phase: str, number: int, head_sha: str
) -> list[str]:
    position = _find_position(project, effort, "effort")
    if position is None:
        return []
    narrative = f"{phase} merged as PR {number} ({head_sha[:12]}); phase closed."
    if record_payload(position).get("position") == narrative:
        return []
    project.supersede(position["id"], payload={"position": narrative})
    return [f"updated the position of effort {effort}"]


def _close_phase_position(project: Project, phase: str) -> list[str]:
    position = _find_position(project, phase, "phase")
    if position is None or record_payload(position).get("status") == "closed":
        return []
    project.supersede(position["id"], payload={"status": "closed"})
    return [f"closed the position of phase {phase}"]
