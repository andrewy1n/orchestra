import json
from collections.abc import Iterable
from pathlib import Path

from orchestra.sessions.session_metrics import read_events
from orchestra.sessions.types import JsonValue, ToolCount, ToolMetrics, TranscriptEvent


def _blocks(event: TranscriptEvent) -> list[dict[str, JsonValue]]:
    message = event.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return []
    return [b for b in content if isinstance(b, dict)]


def _key(name: str, tool_input: JsonValue) -> tuple[str, str]:
    return name, json.dumps(tool_input, sort_keys=True, default=str)


def tool_metrics(events: Iterable[TranscriptEvent]) -> ToolMetrics:
    tools: dict[str, ToolCount] = {}
    pending: dict[str, tuple[str, str]] = {}
    errored: set[tuple[str, str]] = set()
    for event in events:
        for block in _blocks(event):
            kind = block.get("type")
            if kind == "tool_use":
                name = block.get("name")
                if not isinstance(name, str):
                    continue
                key = _key(name, block.get("input"))
                row = tools.setdefault(name, {"calls": 0, "errors": 0, "retries": 0})
                row["calls"] += 1
                if key in errored:
                    row["retries"] += 1
                tool_id = block.get("id")
                if isinstance(tool_id, str):
                    pending[tool_id] = key
            elif kind == "tool_result":
                tool_use_id = block.get("tool_use_id")
                if not isinstance(tool_use_id, str):
                    continue
                key = pending.get(tool_use_id)
                if key is None:
                    continue
                if block.get("is_error") is True:
                    tools[key[0]]["errors"] += 1
                    errored.add(key)
                else:
                    errored.discard(key)
    totals: ToolCount = {
        "calls": sum(row["calls"] for row in tools.values()),
        "errors": sum(row["errors"] for row in tools.values()),
        "retries": sum(row["retries"] for row in tools.values()),
    }
    return {"tools": tools, "totals": totals}


def tool_metrics_for_path(path: Path) -> ToolMetrics:
    return tool_metrics(read_events(path))
