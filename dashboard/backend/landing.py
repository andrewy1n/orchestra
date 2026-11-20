"""Read-only phase Landing git state for the dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from orchestra.conductor.landing import place_of_body
from orchestra.tools.errors import ToolError
from orchestra.tools.git import (
    BranchState,
    Git,
    Merged,
    ReadFailed,
    Unmerged,
    branch_state,
)

_TIMEOUT = 2


@dataclass(frozen=True)
class Landing:
    branch: str
    state: BranchState

    @property
    def exists(self) -> bool:
        return isinstance(self.state, (Merged, Unmerged))

    @property
    def merged(self) -> bool:
        return isinstance(self.state, Merged)

    @property
    def ahead(self) -> int:
        return self.state.ahead if isinstance(self.state, Unmerged) else 0

    @property
    def head(self) -> str:
        return self.state.head if isinstance(self.state, (Merged, Unmerged)) else ""

    @property
    def read_failure(self) -> str | None:
        return self.state.reason if isinstance(self.state, ReadFailed) else None


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
    return Landing(branch, branch_state(root, branch, timeout=_TIMEOUT))
