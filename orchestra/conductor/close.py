"""`orchestra close`: act on a landed phase only after its pull request merges."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from orchestra.canon import record_payload
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.types import Record
from orchestra.conductor.landing import (
    LANDING,
    LandingPlace,
    latest_landing,
    phase_place,
    task_branch,
    task_worktree,
)
from orchestra.score.planning.phase import Phase, current_phase_model
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


@dataclass(frozen=True)
class CloseReport:
    results: tuple[CloseResult, ...]
    errors: tuple[str, ...]
    all_phases: bool

    @classmethod
    def from_outcomes(
        cls, outcomes: tuple[CloseResult | str, ...], *, all_phases: bool
    ) -> CloseReport:
        return cls(
            results=tuple(item for item in outcomes if not isinstance(item, str)),
            errors=tuple(item for item in outcomes if isinstance(item, str)),
            all_phases=all_phases,
        )

    @property
    def refused(self) -> bool:
        return any(item.refusals for item in self.results)

    @property
    def ok(self) -> bool:
        return not self.errors and not self.refused

    @property
    def diagnostics(self) -> tuple[str, ...]:
        refusals = tuple(line for item in self.results for line in item.refusals)
        return refusals + self.errors

    @property
    def exit_code(self) -> int:
        if self.errors:
            return 2
        return 1 if self.refused else 0


def close_phase(
    project: Project,
    repo: Path,
    phase: str,
    states: PullRequestStates,
    cwd: Path | None = None,
) -> CloseResult:
    landing = latest_landing(project.records(), phase)
    if landing is None:
        raise CloseError(f"no landing record for phase {phase!r}; run orchestra land first")
    number = landing.number
    url = landing.url
    state, head_sha = states.pull_request_state(number)
    if state != "MERGED":
        message = f"pull request {number} is {state}; close waits for the merge"
        return CloseResult(phase, number, url, state, head_sha, False, (), message)
    current = _current_phase(project, phase)
    place = phase_place(current, repo)
    refusals = _refusals(place, phase, head_sha, cwd)
    if refusals:
        message = f"pull request {number} is MERGED; close refused"
        return CloseResult(phase, number, url, state, head_sha, False, refusals, message)
    actions = _apply(project, place, current, number, head_sha)
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


def _current_phase(project: Project, phase: str) -> Phase:
    current = current_phase_model(phase, project.records())
    if current is None:
        raise StoreError(f"unknown record: no score:phase with subject {phase!r}")
    return current


def pending_close(project: Project, repo: Path, phase: str) -> bool:
    current = _current_phase(project, phase)
    if current.record["lifecycle_state"] != "done":
        return True
    place = phase_place(current, repo)
    if place.worktree.is_dir() or task_worktrees(place, phase):
        return True
    git = Git(place.repo)
    return git.branch_tip(place.branch) is not None or bool(git.branches(task_branch(phase, "")))


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


def task_worktrees(place: LandingPlace, phase: str) -> tuple[Path, ...]:
    pattern = task_worktree(place, phase, "*")
    if not pattern.parent.is_dir():
        return ()
    return tuple(sorted(path for path in pattern.parent.glob(pattern.name) if path.is_dir()))


def _refusals(place: LandingPlace, phase: str, head_sha: str, cwd: Path | None) -> tuple[str, ...]:
    refusals: list[str] = []
    trees = [place.worktree, *task_worktrees(place, phase)]
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
    git = Git(place.repo)
    phase_branch = place.branch
    tip = git.branch_tip(phase_branch)
    if tip is not None and tip != head_sha:
        refusals.append(
            f"branch {phase_branch} tip {tip[:12]} differs from "
            f"the merged pull request head {head_sha[:12]}"
        )
    reference = tip or head_sha
    for branch in git.branches(task_branch(phase, "")):
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


def _apply(
    project: Project, place: LandingPlace, phase_model: Phase, number: int, head_sha: str
) -> tuple[str, ...]:
    record = phase_model.record
    phase = phase_model.subject
    git = Git(place.repo)
    actions: list[str] = []
    trees = [*task_worktrees(place, phase), place.worktree]
    for tree in trees:
        if tree.is_dir():
            git.remove_worktree(tree)
            actions.append(f"removed worktree {tree}")
    for branch in git.branches(task_branch(phase, "")):
        git.delete_branch(branch)
        actions.append(f"deleted branch {branch}")
    if git.branch_tip(place.branch) is not None:
        git.delete_branch(place.branch)
        actions.append(f"deleted branch {place.branch}")
    steps = _TRANSITIONS.get(record["lifecycle_state"], ())
    if not steps:
        return tuple(actions)
    if phase_model.effort:
        actions.extend(
            _update_effort_position(project, phase_model.effort, phase, number, head_sha)
        )
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
