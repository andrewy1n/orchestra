"""Read-only phase Landing git state for the dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from orchestra.conductor.landing import place_of_body
from orchestra.tools.errors import ToolError
from orchestra.tools.git import Git

_TIMEOUT = 2


@dataclass(frozen=True)
class Landing:
    branch: str
    exists: bool
    ahead: int
    merged: bool
    head: str = field(default="", compare=False)


def landing_branch(body: str, subject: str, root: Path) -> str | None:
    """Branch name from a phase body Landing section, or None when absent."""
    place = place_of_body(subject, body, root)
    return None if place is None else place.branch


def rev_parse_token(root: Path, *refs: str) -> str | None:
    """Joined object names for refs, or None on failure."""
    if not refs:
        return None
    try:
        return Git(root, timeout=_TIMEOUT).resolve_refs(*refs)
    except ToolError:
        return None


def landings_for_phases(root: Path, phases: list[tuple[str, str]]) -> dict[str, Landing]:
    """Map phase subject → Landing for phases whose body has a Landing section."""
    out: dict[str, Landing] = {}
    for subject, body in phases:
        state = phase_landing(root, body, subject)
        if state is not None:
            out[subject] = state
    return out


def phase_landing(root: Path, body: str, subject: str) -> Landing | None:
    branch = landing_branch(body, subject, root)
    if branch is None:
        return None

    git = Git(root, timeout=_TIMEOUT)
    try:
        if not git.is_repository():
            return None
        tip = git.branch_tip(branch)
    except ToolError:
        return None
    if tip is None:
        return Landing(branch=branch, exists=False, ahead=0, merged=False)

    # Unique commits only: patch-equivalent tips (cherry-pick / rebased landing)
    # must not keep Needs you after the work is already on main.
    try:
        cherry = git.run("cherry", "main", branch)
    except ToolError:
        return None
    if cherry.returncode != 0:
        return None
    ahead = sum(1 for line in cherry.stdout.splitlines() if line.startswith("+"))
    merged = ahead == 0

    return Landing(
        branch=branch,
        exists=True,
        ahead=ahead,
        merged=merged,
        head=tip,
    )
