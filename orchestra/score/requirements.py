from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import Record
from orchestra.score.lookups import current_phase, latest_record

SPECIFICATION = "score:specification"

_REQUIREMENTS_HEADING = "## Requirements"
_REQUIREMENT_LINE = re.compile(r"^(R\d+):\s*(.*)$")


def _text(record: Record, key: str) -> str | None:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) and value else None


def acceptance_requirement_ids(record: Record) -> list[str]:
    payload = record_payload(record)
    listed = payload.get("requirements")
    if isinstance(listed, list) and listed:
        return [item for item in listed if isinstance(item, str) and item]
    single = payload.get("requirement")
    return [single] if isinstance(single, str) and single else []


def acceptance_listed_requirements(record: Record) -> list[str] | None:
    if "requirements" not in record_payload(record):
        return None
    return acceptance_requirement_ids(record)


def requirement_lines(text: str) -> dict[str, str]:
    lines: dict[str, str] = {}
    for line in text.splitlines():
        match = _REQUIREMENT_LINE.match(line.strip())
        if match:
            lines[match.group(1)] = line.strip()
    return lines


def requirements_in_body(body: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    inside = False
    done = False
    for line in body.splitlines():
        if line.startswith("## "):
            if inside:
                done = True
            inside = not done and line[3:].strip().casefold() == "requirements"
        elif inside:
            match = _REQUIREMENT_LINE.match(line.strip())
            if match:
                found.append((match.group(1), match.group(2)))
    return found


_REQUIREMENT_LIKE = re.compile(r"^(?:[-*]\s*)?R\d+\b")


def requirement_body_problems(body: str) -> list[str]:
    problems: list[str] = []
    has_section = False
    inside = False
    seen: set[str] = set()
    for line in body.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip() == "Requirements"
            has_section = has_section or inside
            continue
        stripped = line.strip()
        if not inside or not _REQUIREMENT_LIKE.match(stripped):
            continue
        match = _REQUIREMENT_LINE.match(stripped)
        if match is None:
            problems.append(f"malformed requirement line: {stripped!r}")
        elif not match.group(2).strip():
            problems.append(f"{match.group(1)} has no requirement text")
        elif match.group(1) in seen:
            problems.append(f"{match.group(1)} is listed more than once")
        else:
            seen.add(match.group(1))
    if not has_section:
        problems.append("the body has no ## Requirements section")
    elif not seen and not problems:
        problems.append("## Requirements lists no requirement ids")
    return problems


def phase_weight(records: Sequence[Record], phase: str) -> Literal["light", "full"]:
    record = current_phase(phase, records)
    return "light" if record is not None and _text(record, "weight") == "light" else "full"


def phase_requirements(records: Sequence[Record], phase: str) -> list[tuple[str, str]]:
    if phase_weight(records, phase) == "light":
        record = current_phase(phase, records)
        return requirements_in_body(record.get("body", "")) if record is not None else []
    specs = [
        r
        for r in records
        if r["record_type"] == SPECIFICATION
        and r["lifecycle_state"] == "active"
        and _text(r, "phase") == phase
    ]
    spec = latest_record(specs)
    return requirements_in_body(spec.get("body", "")) if spec is not None else []


@dataclass(frozen=True)
class Requirement:
    id: str
    text: str


def read_requirements(record: Record) -> tuple[Requirement, ...]:
    body: object = record.get("body", "")
    if not isinstance(body, str):
        raise RecordShapeError(record["id"], "body", "must be a string")
    if _REQUIREMENTS_HEADING not in body.splitlines():
        return ()
    problems = requirement_body_problems(body)
    if problems:
        raise RecordShapeError(record["id"], "body", problems[0])
    return tuple(Requirement(rid, text) for rid, text in requirements_in_body(body))
