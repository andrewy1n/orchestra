"""Extract identity, time, cost and skill fields from transcript events."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import datetime

from orchestra.sessions.types import JsonValue, SessionFields, TranscriptEvent


def _parse(ts: JsonValue) -> datetime | None:
    if not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _content(event: TranscriptEvent) -> JsonValue:
    message = event.get("message")
    if not isinstance(message, dict):
        return None
    return message.get("content")


def _is_human_prompt(event: TranscriptEvent) -> bool:
    if event.get("isMeta") or event.get("isSidechain"):
        return False
    content = _content(event)
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return any(
            isinstance(block, dict) and block.get("type") != "tool_result" for block in content
        )
    return False


def _skill_names(event: TranscriptEvent) -> Iterable[str]:
    content = _content(event)
    if not isinstance(content, list):
        return
    for block in content:
        if (
            isinstance(block, dict)
            and block.get("type") == "tool_use"
            and block.get("name") == "Skill"
        ):
            tool_input = block.get("input")
            name = tool_input.get("skill") if isinstance(tool_input, dict) else None
            if isinstance(name, str) and name:
                yield name


def session_fields(events: Iterable[TranscriptEvent]) -> SessionFields:
    session_id = cwd = branch = None
    first = last = None
    turns = 0
    cost = None
    skills: Counter[str] = Counter()
    for event in events:
        session_id = session_id or event.get("sessionId")
        cwd = cwd or event.get("cwd")
        branch = branch or event.get("gitBranch")
        kind = event.get("type")
        if kind == "cost-state":
            value = event.get("totalCostUSD")
            if isinstance(value, (int, float)):
                cost = float(value)
            continue
        timestamp = event.get("timestamp")
        stamp = _parse(timestamp)
        if stamp is not None:
            raw = timestamp
            if not isinstance(raw, str):
                continue
            if first is None or stamp < first[0]:
                first = (stamp, raw)
            if last is None or stamp > last[0]:
                last = (stamp, raw)
        if kind == "user" and _is_human_prompt(event):
            turns += 1
        elif kind == "assistant":
            skills.update(_skill_names(event))
    return {
        "session_id": session_id,
        "cwd": cwd,
        "branch": branch,
        "start": first[1] if first else None,
        "end": last[1] if last else None,
        "duration_seconds": (last[0] - first[0]).total_seconds() if first and last else None,
        "turns": turns,
        "cost_usd": cost,
        "skills": dict(skills),
    }
