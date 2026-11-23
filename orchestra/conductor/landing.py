"""Read `conductor:landing` records written by `orchestra land`."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.fields import optional_text, required_int, required_text
from orchestra.canon.sections import body_sections
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.verification.evidence.revision import revision_matches
from orchestra.score.lookups import corrected_ids, latest_record
from orchestra.score.planning.phase import Phase

LANDING = "conductor:landing"
PROOF_PACKET = "conductor:proof-packet"

LandingProofState = Literal["landed", "no-landing", "failed", "no-packet", "not-at-head"]


@dataclass(frozen=True)
class Landing:
    id: str
    phase: str
    effort: str | None
    number: int
    url: str
    head_sha: str | None
    result: Literal["success", "fail", "blocked", "skipped"]
    recorded_at: str
    record: Record


@dataclass(frozen=True)
class ProofPacket:
    id: str
    phase: str
    effort: str | None
    revision: str
    base: str | None
    kind: str
    recorded_at: str
    record: Record


def _result(
    record: Record, payload: JsonObject
) -> Literal["success", "fail", "blocked", "skipped"]:
    value = required_text(record, payload, "result")
    if value == "success" or value == "fail" or value == "blocked" or value == "skipped":
        return value
    raise RecordShapeError(record["id"], "result", "must be success, fail, blocked or skipped")


def read_landing(record: Record) -> Landing:
    payload = record_payload(record)
    result = _result(record, payload)
    return Landing(
        id=record["id"],
        phase=required_text(record, payload, "phase"),
        effort=optional_text(record, payload, "effort"),
        number=required_int(record, payload, "number"),
        url=required_text(record, payload, "url"),
        head_sha=(
            required_text(record, payload, "head_sha")
            if result == "success"
            else optional_text(record, payload, "head_sha")
        ),
        result=result,
        recorded_at=record.get("recorded_at", ""),
        record=record,
    )


def read_proof_packet(record: Record) -> ProofPacket:
    payload = record_payload(record)
    return ProofPacket(
        id=record["id"],
        phase=required_text(record, payload, "phase"),
        effort=optional_text(record, payload, "effort"),
        revision=required_text(record, payload, "revision"),
        base=optional_text(record, payload, "base"),
        kind=required_text(record, payload, "kind"),
        recorded_at=record.get("recorded_at", ""),
        record=record,
    )


def latest_landing(records: Sequence[Record], phase: str) -> Landing | None:
    """Return the newest landing for a phase, or None."""
    record = latest_record(
        [
            record
            for record in records
            if record["record_type"] == LANDING and record_payload(record).get("phase") == phase
        ]
    )
    return read_landing(record) if record is not None else None


def landing_payload(
    phase: str, number: int, url: str, head_sha: str, result: str, effort: str | None
) -> JsonObject:
    payload: JsonObject = {
        "phase": phase,
        "number": number,
        "url": url,
        "head_sha": head_sha,
        "result": result,
    }
    if effort:
        payload["effort"] = effort
    return payload


_SECTIONS = (
    ("problem", "Problem"),
    ("approach", "Approach"),
    ("exit_criteria", "Exit criteria"),
)


def describe_phase(phase: Record) -> dict[str, str]:
    """Read the Problem, Approach and Exit criteria sections of a phase body."""
    sections = body_sections(phase.get("body") or "")
    found = {key: sections.get(heading, "") for key, heading in _SECTIONS}
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


def _place(slug: str, spec: LandingSpec, store: Path) -> LandingPlace:
    return LandingPlace(
        repo=landing_repo(store, spec),
        worktree=landing_worktree(store, slug, spec),
        branch=spec.branch or f"phase/{slug}",
        base=spec.base or "main",
    )


def phase_place(phase: Phase, store: Path) -> LandingPlace:
    """Return where a phase lands; a body with no Landing section gives the default layout."""
    return _place(phase.subject, parse_landing(phase.body), store)


def place_of_body(slug: str, body: str, store: Path) -> LandingPlace | None:
    spec = parse_landing(body)
    if not spec.present:
        return None
    return _place(slug, spec, store)


def landing_place(phase: Phase, store: Path) -> LandingPlace | None:
    """Return where a phase lands, or None when its body has no Landing section."""
    return place_of_body(phase.subject, phase.body, store)


def task_worktree(place: LandingPlace, phase: str, task: str) -> Path:
    return place.repo / ".worktrees" / f"{phase}--{task}"


def task_branch(phase: str, task: str) -> str:
    return f"task/{phase}/{task}"


def _effort(record: Record) -> str | None:
    value = record_payload(record).get("effort")
    return value if isinstance(value, str) and value else None


def _belongs(packet: Record, slug: str, effort: str | None, corrected: set[str]) -> bool:
    if packet["id"] in corrected or record_payload(packet).get("phase") != slug:
        return False
    packet_effort = _effort(packet)
    return packet_effort is None or packet_effort == effort


def belongs_to_phase(records: Sequence[Record], phase: Record, packet: Record) -> bool:
    return _belongs(packet, phase["subject"], _effort(phase), corrected_ids(records))


def _latest_packet_record(
    records: Sequence[Record], slug: str, effort: str | None, head: str | None
) -> Record | None:
    corrected = corrected_ids(records)
    return latest_record(
        [
            record
            for record in records
            if record["record_type"] == PROOF_PACKET
            and _belongs(record, slug, effort, corrected)
            and (
                head is None or revision_matches(str(record_payload(record).get("revision")), head)
            )
        ]
    )


def proof_packet(
    records: Sequence[Record], phase: Phase, head: str | None = None
) -> ProofPacket | None:
    """Return the latest belonging proof packet, at `head` when one is given."""
    record = _latest_packet_record(records, phase.subject, phase.effort, head)
    return read_proof_packet(record) if record is not None else None


class LandingProofError(ValueError):
    def __init__(self, record_id: str, field: str) -> None:
        super().__init__(f"{record_id}: payload field {field!r} is missing or not a string")
        self.record_id = record_id
        self.field = field


def landing_proof_state(records: Sequence[Record], phase: Phase) -> LandingProofState:
    """Decide where a phase's latest landing stands against its latest proof packet."""
    landing = latest_landing(records, phase.subject)
    if landing is None:
        return "no-landing"
    if landing.result != "success":
        return "failed"
    try:
        packet = proof_packet(records, phase)
    except RecordShapeError as error:
        if error.field != "revision":
            raise
        raise LandingProofError(error.record_id, error.field) from error
    if packet is None:
        return "no-packet"
    return "landed" if revision_matches(landing.head_sha or "", packet.revision) else "not-at-head"
