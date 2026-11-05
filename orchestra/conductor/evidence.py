"""The JSON evidence block an executor returns to the parent session."""

from __future__ import annotations

import json
from pathlib import Path

from orchestra.canon.types import JsonObject, JsonValue

KINDS = ("deliver", "repair", "evaluate", "incidental")
RESULTS = ("pass", "fail", "blocked", "abandoned")
VERDICTS = ("pass", "fail", "delta", "inconclusive")
REQUIRED = ("subject", "kind", "result", "verdict", "evidence")
TEXT_FIELDS = (
    "subject",
    "revision",
    "evidence",
    "observations",
    "root_cause",
    "metrics",
    "claim",
    "attempted_action",
    "retry_when",
    "blocker",
)

EVIDENCE_SCHEMA: JsonObject = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "orchestra task evidence",
    "type": "object",
    "additionalProperties": False,
    "required": list(REQUIRED),
    "properties": {
        **{name: {"type": "string"} for name in TEXT_FIELDS},
        "kind": {"enum": list(KINDS)},
        "result": {"enum": list(RESULTS)},
        "verdict": {"enum": list(VERDICTS)},
        "needs_human": {"type": "boolean"},
    },
}


class EvidenceError(ValueError):
    """The evidence file is not a valid evidence block."""


def parse_evidence(path: Path) -> JsonObject:
    try:
        data: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read evidence {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise EvidenceError("evidence must be a JSON object")
    problems: list[str] = []
    problems += [f"missing required field {name!r}" for name in REQUIRED if name not in data]
    problems += [f"unknown field {name!r}" for name in data if name not in _known()]
    for name in TEXT_FIELDS:
        if name in data and not isinstance(data[name], str):
            problems.append(f"field {name!r} must be a string")
    if "needs_human" in data and not isinstance(data["needs_human"], bool):
        problems.append("field 'needs_human' must be a boolean")
    for name, allowed in (("kind", KINDS), ("result", RESULTS), ("verdict", VERDICTS)):
        if name in data and data[name] not in allowed:
            problems.append(f"field {name!r} must be one of {', '.join(allowed)}")
    if problems:
        raise EvidenceError("; ".join(problems))
    return data


def _known() -> set[str]:
    return {*TEXT_FIELDS, "kind", "result", "verdict", "needs_human"}


def evidence_body(evidence: JsonObject) -> str:
    return "\n".join(f"{name}: {value}" for name, value in evidence.items())
