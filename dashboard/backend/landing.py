"""Read-only phase Landing git state for the dashboard."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from orchestra.tools.errors import ToolError
from orchestra.tools.git import Git

_TIMEOUT = 2
_LANDING_HEADING = re.compile(r"^##\s+Landing\s*$")
_NEXT_HEADING = re.compile(r"^##\s+")
_BRANCH_BACKTICK = re.compile(r"(?i)branch[^`\n]*`([^`]+)`")


@dataclass(frozen=True)
class Landing:
    branch: str
    exists: bool
    ahead: int
    merged: bool
    head: str = field(default="", compare=False)


def _landing_section(body: str) -> str | None:
    lines = body.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if _LANDING_HEADING.match(line):
            start = index + 1
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start, len(lines)):
        if _NEXT_HEADING.match(lines[index]):
            end = index
            break
    return "\n".join(lines[start:end])


def _branch_name(section: str, subject: str) -> str:
    match = _BRANCH_BACKTICK.search(section)
    if match:
        return match.group(1).strip()
    return f"phase/{subject}"


def landing_branch(body: str, subject: str) -> str | None:
    """Branch name from a phase body Landing section, or None when absent."""
    section = _landing_section(body)
    if section is None:
        return None
    return _branch_name(section, subject)


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
    section = _landing_section(body)
    if section is None:
        return None
    branch = _branch_name(section, subject)

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
