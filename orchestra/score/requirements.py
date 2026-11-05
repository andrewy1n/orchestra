from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Literal

from orchestra.canon import record_payload
from orchestra.canon.types import Record

PHASE = "score:phase"
SPECIFICATION = "score:specification"

_REQUIREMENT_LINE = re.compile(r"^(R\d+):\s*(.*)$")


def _text(record: Record, key: str) -> str | None:
    value = record_payload(record).get(key)
    return value if isinstance(value, str) and value else None


def _latest(records: Sequence[Record]) -> Record | None:
    latest: Record | None = None
    for record in records:
        if latest is None or record["recorded_at"] >= latest["recorded_at"]:
            latest = record
    return latest


def acceptance_requirement_ids(record: Record) -> list[str]:
    payload = record_payload(record)
    listed = payload.get("requirements")
    if isinstance(listed, list):
        return [item for item in listed if isinstance(item, str) and item]
    single = payload.get("requirement")
    return [single] if isinstance(single, str) and single else []


def requirements_in_body(body: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    inside = False
    for line in body.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip() == "Requirements"
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


def _phase_record(records: Sequence[Record], phase: str) -> Record | None:
    return _latest([r for r in records if r["record_type"] == PHASE and r["subject"] == phase])


def phase_weight(records: Sequence[Record], phase: str) -> Literal["light", "full"]:
    record = _phase_record(records, phase)
    return "light" if record is not None and _text(record, "weight") == "light" else "full"


def phase_requirements(records: Sequence[Record], phase: str) -> list[tuple[str, str]]:
    if phase_weight(records, phase) == "light":
        record = _phase_record(records, phase)
        return requirements_in_body(record.get("body", "")) if record is not None else []
    specs = [
        r
        for r in records
        if r["record_type"] == SPECIFICATION
        and r["lifecycle_state"] == "active"
        and _text(r, "phase") == phase
    ]
    spec = _latest(specs)
    return requirements_in_body(spec.get("body", "")) if spec is not None else []
