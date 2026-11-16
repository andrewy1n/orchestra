"""Read `conductor:landing` records written by `orchestra land`."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon import record_payload
from orchestra.canon.query import latest
from orchestra.canon.types import Record
from orchestra.conductor.revision import revision_matches

LANDING = "conductor:landing"
PROOF_PACKET = "conductor:proof-packet"


def latest_landing(records: Sequence[Record], phase: str) -> Record | None:
    """Return the newest landing record for a phase, or None."""
    found = [
        record
        for record in records
        if record["record_type"] == LANDING and record_payload(record).get("phase") == phase
    ]
    if not found:
        return None
    return max(enumerate(found), key=lambda pair: (pair[1].get("recorded_at", ""), pair[0]))[1]


_HEADING = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
_SECTIONS = (
    ("problem", "Problem"),
    ("approach", "Approach"),
    ("exit_criteria", "Exit criteria"),
)


def _section(body: str, name: str) -> str:
    headings = list(_HEADING.finditer(body))
    for index, heading in enumerate(headings):
        if heading.group(1) == name:
            end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
            return body[heading.end() : end].strip()
    return ""


def describe_phase(phase: Record) -> dict[str, str]:
    """Read the Problem, Approach and Exit criteria sections of a phase body."""
    body = phase.get("body") or ""
    found = {key: _section(body, heading) for key, heading in _SECTIONS}
    return {key: text for key, text in found.items() if text}


def pull_request_title(phase: Record) -> str:
    title = record_payload(phase).get("title")
    name = title if isinstance(title, str) and title else phase["subject"]
    return f"{name} ({phase['subject']})"


def _demote(markdown: str) -> str:
    return re.sub(r"^(#{2,5}) ", r"#\1 ", markdown, flags=re.MULTILINE)


def _without_diff(markdown: str) -> str:
    return re.sub(r"(?ms)^## Diff\s*$.*?(?=^## |\Z)", "", markdown).strip()


def pull_request_body(description: Mapping[str, str], packet: str) -> str:
    """Say what the pull request is for, then include proof without its diff."""
    parts: list[str] = []
    if description.get("problem"):
        parts.append(f"## What this PR is for\n\n{description['problem']}")
    if description.get("approach"):
        parts.append(f"## Approach\n\n{description['approach']}")
    if description.get("exit_criteria"):
        parts.append(f"## Exit criteria\n\n{description['exit_criteria']}")
    parts.append(f"## Proof packet\n\n{_demote(_without_diff(packet.strip()))}")
    return "\n\n".join(parts) + ("\n" if parts else "")


_LANDING_HEADING = re.compile(r"^##\s+Landing\s*$")
_NEXT_HEADING = re.compile(r"^##\s+")
_LANDING_LINE = re.compile(
    r"^(?:[-*]\s+)?(repo|worktree|branch|base)\s*:\s*(.+?)\s*$", re.IGNORECASE
)


@dataclass(frozen=True)
class LandingSpec:
    present: bool = False
    repo: str = ""
    worktree: str = ""
    branch: str = ""
    base: str = ""


@dataclass(frozen=True)
class LandingPlace:
    repo: Path
    worktree: Path
    branch: str
    base: str


def _unwrap(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()
    return text


def parse_landing(body: str) -> LandingSpec:
    """Read `Repo:`, `Worktree:`, `Branch:` and `Base:` lines from the `## Landing` section."""
    inside = False
    found = False
    values: dict[str, str] = {}
    for line in body.splitlines():
        if _LANDING_HEADING.match(line):
            inside = True
            found = True
            continue
        if inside and _NEXT_HEADING.match(line):
            break
        if not inside:
            continue
        match = _LANDING_LINE.match(line.strip())
        if match:
            values.setdefault(match.group(1).lower(), _unwrap(match.group(2)))
    return LandingSpec(
        present=found,
        repo=values.get("repo", ""),
        worktree=values.get("worktree", ""),
        branch=values.get("branch", ""),
        base=values.get("base", ""),
    )


def _resolve_path(store: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else store / path


def landing_repo(store: Path, landing: LandingSpec) -> Path:
    if not landing.repo:
        return store
    return _resolve_path(store, landing.repo)


def landing_worktree(store: Path, phase_slug: str, landing: LandingSpec) -> Path:
    if landing.worktree:
        return _resolve_path(store, landing.worktree)
    return landing_repo(store, landing) / ".worktrees" / phase_slug


def phase_place(phase: Record, store: Path) -> LandingPlace:
    """Return where a phase lands; a body with no Landing section gives the default layout."""
    spec = parse_landing(phase.get("body") or "")
    slug = phase["subject"]
    return LandingPlace(
        repo=landing_repo(store, spec),
        worktree=landing_worktree(store, slug, spec),
        branch=spec.branch or f"phase/{slug}",
        base=spec.base or "main",
    )


def landing_place(phase: Record, store: Path) -> LandingPlace | None:
    """Return where a phase lands, or None when its body has no Landing section."""
    if not parse_landing(phase.get("body") or "").present:
        return None
    return phase_place(phase, store)


def task_worktree(place: LandingPlace, phase: str, task: str) -> Path:
    return place.repo / ".worktrees" / f"{phase}--{task}"


def task_branch(phase: str, task: str) -> str:
    return f"task/{phase}/{task}"


def _corrected_ids(records: Sequence[Record]) -> set[str]:
    return {
        target
        for record in records
        for target in (record.get("relationships") or {}).get("corrects") or []
    }


def _effort(record: Record) -> str | None:
    value = record_payload(record).get("effort")
    return value if isinstance(value, str) and value else None


def _belongs(packet: Record, slug: str, effort: str | None, corrected: set[str]) -> bool:
    if packet["id"] in corrected or record_payload(packet).get("phase") != slug:
        return False
    packet_effort = _effort(packet)
    return packet_effort is None or packet_effort == effort


def belongs_to_phase(records: Sequence[Record], phase: Record, packet: Record) -> bool:
    return _belongs(packet, phase["subject"], _effort(phase), _corrected_ids(records))


def proof_packet(
    records: Sequence[Record], phase: Record, head: str | None = None
) -> Record | None:
    """Return the latest belonging proof packet, at `head` when one is given."""
    slug = phase["subject"]
    effort = _effort(phase)
    corrected = _corrected_ids(records)
    found = [
        record
        for record in records
        if record["record_type"] == PROOF_PACKET
        and _belongs(record, slug, effort, corrected)
        and (head is None or revision_matches(str(record_payload(record).get("revision")), head))
    ]
    return latest(found)
