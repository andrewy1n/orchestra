"""Stream Claude Code session transcripts as JSONL events."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TypeGuard

from orchestra.sessions.session_types import JsonObject, JsonValue, TranscriptEvent


@dataclass
class ReadStats:
    bad_lines: int = 0


def _is_json_array(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _is_json_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def _json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if _is_json_array(value):
        return [_json_value(raw) for raw in value]
    if _is_json_object(value):
        result: JsonObject = {}
        for key, raw in value.items():
            result[key] = _json_value(raw)
        return result
    return None


def read_events(path: Path, stats: ReadStats | None = None) -> Iterator[TranscriptEvent]:
    stats = stats if stats is not None else ReadStats()
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                event: object = json.loads(line)
            except ValueError:
                stats.bad_lines += 1
                continue
            if not _is_json_object(event):
                stats.bad_lines += 1
                continue
            normalized = _json_value(event)
            if not isinstance(normalized, dict):
                stats.bad_lines += 1
                continue
            yield TranscriptEvent(**normalized)
