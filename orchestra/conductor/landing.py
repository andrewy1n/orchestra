"""Read `conductor:landing` records written by `orchestra land`."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from orchestra.canon import record_payload
from orchestra.canon.types import Record

LANDING = "conductor:landing"


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
